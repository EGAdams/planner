#!/usr/bin/env python3
"""Cross-platform launcher for the planner development servers.

This script replaces the old Python snippet that only targeted the WSL stack.
When invoked in Windows mode it starts every server natively (letta, the
orchestrator and dashboard agents, the dashboard UI, and the expense
categorizer API).  A WSL mode is also available so we can preserve the existing
workflow when needed.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import platform
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

PLANNER_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PLANNER_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS = platform.system().lower().startswith("win")
CREATE_NEW_PROCESS_GROUP = subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0

PYTHON_REQUIREMENT_FILES = [
    PLANNER_ROOT / "requirements.txt",
    PLANNER_ROOT / "nonprofit_finance_db" / "requirements.txt",
]

# Extra Windows-specific packages that are not yet captured in the shared
# requirements files but are necessary for the orchestrator and supporting
# services to run on Windows.
PYTHON_EXTRA_PACKAGES = [
    "google-genai>=0.6.0",
    "requests>=2.32.0",
    "fastapi==0.115.6",
    "uvicorn>=0.30.0",
    "sse-starlette>=1.6.5",
    "python-dotenv>=1.0.0",
    "letta>=0.8.0",
    "asyncpg>=0.29.0",
]

WINDOWS_BOOTSTRAP_VERSION = 2
PY_BOOTSTRAP_SENTINEL = PLANNER_ROOT / ".windows_python_bootstrap"
DASHBOARD_DIR = PLANNER_ROOT / "dashboard"
DASHBOARD_DIST = DASHBOARD_DIR / "backend" / "dist" / "server.js"


@dataclass
class ManagedProcess:
    name: str
    process: subprocess.Popen[str]
    log_path: Path
    log_handle: io.TextIOWrapper


def run_bootstrap_command(cmd: Sequence[str], cwd: Path | None = None) -> None:
    """Run a setup command with helpful logging."""
    location = f" (cwd={cwd})" if cwd else ""
    print(f"[BOOTSTRAP] {' '.join(cmd)}{location}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def _current_bootstrap_version() -> int:
    if not PY_BOOTSTRAP_SENTINEL.exists():
        return 0
    try:
        data = json.loads(PY_BOOTSTRAP_SENTINEL.read_text())
    except Exception:
        return 0
    return int(data.get("version", 0))


def ensure_python_dependencies(python_exe: str, force: bool = False) -> None:
    """Install Python dependencies required by the Windows stack."""
    sentinel_version = _current_bootstrap_version()
    if sentinel_version >= WINDOWS_BOOTSTRAP_VERSION and not force:
        print(
            "[BOOTSTRAP] Python dependencies already installed "
            f"(remove {PY_BOOTSTRAP_SENTINEL.name} or pass --force-bootstrap to re-run)."
        )
        return

    pip_cmd = [python_exe, "-m", "pip"]
    run_bootstrap_command(pip_cmd + ["install", "--upgrade", "pip"])

    for req in PYTHON_REQUIREMENT_FILES:
        if req.exists():
            run_bootstrap_command(pip_cmd + ["install", "-r", str(req)])

    if PYTHON_EXTRA_PACKAGES:
        run_bootstrap_command(pip_cmd + ["install"] + PYTHON_EXTRA_PACKAGES)

    sentinel_payload = {
        "version": WINDOWS_BOOTSTRAP_VERSION,
        "completed_at": datetime.now().isoformat(),
    }
    PY_BOOTSTRAP_SENTINEL.write_text(json.dumps(sentinel_payload, indent=2))
    print(f"[BOOTSTRAP] Wrote sentinel to {PY_BOOTSTRAP_SENTINEL}")


def ensure_node_dependencies(npm_executable: str) -> None:
    """Make sure the dashboard backend has been built before starting."""
    node_modules = DASHBOARD_DIR / "node_modules"
    if not node_modules.exists():
        run_bootstrap_command([npm_executable, "install"], cwd=DASHBOARD_DIR)
    if not DASHBOARD_DIST.exists():
        run_bootstrap_command([npm_executable, "run", "build"], cwd=DASHBOARD_DIR)


def bootstrap_windows_stack(
    args: argparse.Namespace, python_exe: str, npm_executable: str
) -> None:
    """Install dependencies required to run the Windows stack."""
    if args.skip_bootstrap:
        print("[BOOTSTRAP] Skipping dependency setup (--skip-bootstrap).")
        return

    ensure_python_dependencies(python_exe, force=args.force_bootstrap)
    ensure_node_dependencies(npm_executable)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start the planner servers either natively on Windows or via WSL."
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "windows", "wsl"],
        default="auto",
        help="Which stack to boot. Defaults to auto-detect based on the host OS.",
    )
    parser.add_argument(
        "--dashboard-port",
        type=int,
        default=3000,
        help="Port to expose the admin dashboard on (Windows mode).",
    )
    parser.add_argument(
        "--letta-port",
        type=int,
        default=8283,
        help="Port used by the Letta memory server.",
    )
    parser.add_argument(
        "--python",
        help="Explicit Python interpreter to use in Windows mode (defaults to .venv or sys.executable).",
    )
    parser.add_argument(
        "--letta-command",
        help="Override the command used to start Letta in Windows mode (example: 'poetry run letta server').",
    )
    parser.add_argument(
        "--standalone-letta",
        action="store_true",
        help="Also start an extra dedicated Letta server after the other services (mirrors the legacy './letta server' call).",
    )
    parser.add_argument(
        "--wsl-root",
        default="/home/adamsl/planner",
        help="Root path of this repo inside WSL (only used in WSL mode).",
    )
    parser.add_argument(
        "--wsl-distro",
        default="Ubuntu",
        help="Name of the WSL distribution to target.",
    )
    parser.add_argument(
        "--wsl-user",
        default="adamsl",
        help="User to run WSL commands as.",
    )
    parser.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="Skip dependency setup (use if you've already installed everything).",
    )
    parser.add_argument(
        "--force-bootstrap",
        action="store_true",
        help="Force dependency setup even if the sentinel file exists.",
    )
    parser.add_argument(
        "--skip-letta",
        action="store_true",
        help="Skip starting Letta services (useful when Postgres isn't available).",
    )
    return parser.parse_args()


def determine_mode(preference: str) -> str:
    if preference == "auto":
        return "windows" if WINDOWS else "wsl"
    return preference


def resolve_python_executable(explicit: str | None) -> str:
    candidates: List[str] = []
    if explicit:
        candidates.append(explicit)
    env_python = os.environ.get("PYTHON_FOR_PLANNER")
    if env_python:
        candidates.append(env_python)

    venv_dir = PLANNER_ROOT / ".venv"
    if WINDOWS:
        candidates.append(str(venv_dir / "Scripts" / "python.exe"))
    else:
        candidates.append(str(venv_dir / "bin" / "python"))

    candidates.append(sys.executable)

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(Path(candidate))

    fallback = shutil.which("python") or shutil.which("python3")
    if fallback:
        return fallback
    raise RuntimeError("Unable to locate a Python interpreter. Set --python to continue.")


def resolve_executable(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    raise RuntimeError(f"Unable to find '{name}' on PATH. Please install it before continuing.")


def build_letta_command(args: argparse.Namespace, python_exe: str) -> Sequence[str]:
    if args.letta_command:
        return shlex.split(args.letta_command)
    env_override = os.environ.get("LETTA_CMD")
    if env_override:
        return shlex.split(env_override)
    executable = shutil.which("letta")
    if executable:
        return [executable, "server"]
    # Fall back to python -m letta if CLI entry point is not on PATH.
    return [python_exe, "-m", "letta", "server"]


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def get_database_url(env: dict) -> str | None:
    for key in ("DATABASE_URL", "LETTADB_URL", "LETTADB_CONNECTION"):
        value = env.get(key)
        if value:
            return value
    return None


def can_connect_to_database(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5432
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


def find_windows_pid_on_port(port: int) -> int | None:
    if not WINDOWS:
        return None
    try:
        output = subprocess.check_output(
            ["netstat", "-ano", "-p", "tcp"], text=True, stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line.upper().startswith("TCP"):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        local_addr, _, _, state, pid_str = parts[:5]
        if state.upper() != "LISTENING":
            continue
        if local_addr.endswith(f":{port}"):
            try:
                return int(pid_str)
            except ValueError:
                return None
    return None


def open_log(log_name: str):
    log_path = LOG_DIR / log_name
    try:
        handle = open(log_path, "w", encoding="utf-8", buffering=1)
    except OSError as exc:
        raise RuntimeError(f"Unable to open log file {log_path}: {exc}") from exc
    return log_path, handle


def start_process(
    name: str,
    cmd: Sequence[str],
    cwd: Path,
    log_name: str,
    env: dict | None = None,
) -> ManagedProcess:
    log_path, log_handle = open_log(log_name)
    try:
        process = subprocess.Popen(
            list(cmd),
            cwd=str(cwd),
            env=env or os.environ.copy(),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NEW_PROCESS_GROUP,
        )
    except FileNotFoundError as exc:
        log_handle.close()
        raise RuntimeError(f"Unable to start {name}: {exc}") from exc

    print(f"[STARTED] {name} (PID {process.pid}) -> {log_path}")
    return ManagedProcess(name=name, process=process, log_path=log_path, log_handle=log_handle)


def terminate_process(record: ManagedProcess) -> None:
    proc = record.process
    if proc.poll() is not None:
        return

    print(f"[STOPPING] {record.name} (PID {proc.pid})")
    try:
        if WINDOWS:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
            time.sleep(0.5)
    except Exception:
        pass

    if proc.poll() is None:
        proc.terminate()
        time.sleep(0.5)

    if proc.poll() is None:
        proc.kill()


def monitor_processes(processes: List[ManagedProcess]) -> None:
    if not processes:
        print("No processes were started.")
        return

    print("\nAll services launched. Press Ctrl+C to stop everything.\n")
    try:
        while processes:
            for record in list(processes):
                if record.process.poll() is not None:
                    print(f"[EXITED] {record.name} (code {record.process.returncode})")
                    record.log_handle.close()
                    processes.remove(record)
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nReceived interrupt. Shutting down servers...")
        for record in processes:
            terminate_process(record)
        time.sleep(0.5)
    finally:
        for record in processes:
            record.log_handle.close()
        print("All servers have been stopped.")


def start_windows_services(
    args: argparse.Namespace, python_exe: str | None = None, npm_executable: str | None = None
) -> List[ManagedProcess]:
    if not WINDOWS:
        raise RuntimeError("Windows mode can only be used on Windows hosts.")

    python_exe = python_exe or resolve_python_executable(args.python)
    npm_executable = npm_executable or resolve_executable("npm")

    base_env = os.environ.copy()
    processes: List[ManagedProcess] = []

    letta_env = base_env.copy()

    # Check if user explicitly skipped Letta
    if args.skip_letta:
        print("[SKIP] --skip-letta provided. Not starting Letta.")
    # Check if Letta is already running
    elif is_port_in_use(args.letta_port):
        print(
            f"[SKIP] Letta server already running on port {args.letta_port}. "
            "Use --letta-port to specify a different port if needed."
        )
    else:
        # Check if PostgreSQL is configured and reachable
        database_url = get_database_url(letta_env)
        if database_url and not can_connect_to_database(database_url):
            print(
                f"[WARNING] DATABASE_URL is set but unreachable. "
                f"Letta will fall back to SQLite at ~/.letta/letta.db"
            )

        # Start Letta (supports both SQLite default and PostgreSQL via env vars)
        processes.append(
            start_process(
                name="Letta (Unified Memory)",
                cmd=build_letta_command(args, python_exe),
                cwd=PLANNER_ROOT,
                log_name="windows_letta.log",
                env=letta_env,
            )
        )

    # Orchestrator agent
    processes.append(
        start_process(
            name="Orchestrator Agent",
            cmd=[python_exe, "main.py"],
            cwd=PLANNER_ROOT / "orchestrator_agent",
            log_name="windows_orchestrator_agent.log",
            env=base_env,
        )
    )

    # System Admin dashboard (React/Node)
    dashboard_env = base_env.copy()
    dashboard_env.setdefault("ADMIN_PORT", str(args.dashboard_port))
    existing_dashboard_pid = find_windows_pid_on_port(args.dashboard_port)
    if existing_dashboard_pid:
        print(
            f"[SKIP] Port {args.dashboard_port} is already in use (PID {existing_dashboard_pid}). "
            "Leaving the existing dashboard process running. Use --dashboard-port to pick another port."
        )
    else:
        processes.append(
            start_process(
                name=f"System Admin Dashboard (port {args.dashboard_port})",
                cmd=[npm_executable, "start"],
                cwd=PLANNER_ROOT / "dashboard",
                log_name="windows_dashboard.log",
                env=dashboard_env,
            )
        )

    # Dashboard Ops agent (waits for dashboard to come online before self-bootstrapping)
    ops_env = base_env.copy()
    ops_env.setdefault("OPS_AGENT_BOOTSTRAP_GRACE", "12")
    ops_env.setdefault("PLANNER_ROOT", str(PLANNER_ROOT))
    processes.append(
        start_process(
            name="Dashboard Ops Agent",
            cmd=[python_exe, "main.py"],
            cwd=PLANNER_ROOT / "dashboard_ops_agent",
            log_name="windows_dashboard_ops.log",
            env=ops_env,
        )
    )

    # Expense categorizer API server
    processes.append(
        start_process(
            name="Daily Expense Categorizer API",
            cmd=[python_exe, "api_server.py"],
            cwd=PLANNER_ROOT / "nonprofit_finance_db",
            log_name="windows_expense_api.log",
            env=base_env,
        )
    )

    # Optional standalone Letta server, mimicking the legacy `./letta server` call.
    if args.standalone_letta:
        if is_port_in_use(args.letta_port):
            print(
                f"[SKIP] Port {args.letta_port} already in use. "
                "Assuming the unified Letta server is running; skipping standalone launch."
            )
        else:
            processes.append(
                start_process(
                    name="Letta Server (standalone)",
                    cmd=build_letta_command(args, python_exe),
                    cwd=PLANNER_ROOT,
                    log_name="windows_letta_standalone.log",
                    env=base_env,
                )
            )

    return processes


def build_wsl_command(raw_command: str, args: argparse.Namespace) -> List[str]:
    cmd: List[str] = ["wsl"]
    if args.wsl_distro:
        cmd.extend(["-d", args.wsl_distro])
    if args.wsl_user:
        cmd.extend(["-u", args.wsl_user])
    cmd.extend(["bash", "-lc", raw_command])
    return cmd


def start_wsl_services(args: argparse.Namespace) -> List[ManagedProcess]:
    if shutil.which("wsl") is None:
        raise RuntimeError("Unable to find the 'wsl' command. Install WSL or use Windows mode.")

    processes: List[ManagedProcess] = []
    commands = [
        (
            "Non-profit System Dashboard (A2A)",
            f"cd {args.wsl_root} && ./start_a2a_system.sh",
            "wsl_a2a.log",
        ),
        (
            "Daily Expense Categorizer API",
            f"cd {args.wsl_root} && ./office-assistant/start_server.sh",
            "wsl_expense_api.log",
        ),
        (
            "Letta Server",
            f"cd {args.wsl_root} && ./letta server",
            "wsl_letta.log",
        ),
    ]

    for name, raw_cmd, log_name in commands:
        processes.append(
            start_process(
                name=name,
                cmd=build_wsl_command(raw_cmd, args),
                cwd=PLANNER_ROOT,
                log_name=log_name,
            )
        )

    return processes


def main() -> None:
    args = parse_args()
    mode = determine_mode(args.mode)

    print(f"Planner root: {PLANNER_ROOT}")
    print(f"Log directory: {LOG_DIR}")
    print(f"Selected mode: {mode}")

    if mode == "windows":
        python_exe = resolve_python_executable(args.python)
        npm_executable = resolve_executable("npm")
        bootstrap_windows_stack(args, python_exe, npm_executable)
        processes = start_windows_services(args, python_exe, npm_executable)
    elif mode == "wsl":
        processes = start_wsl_services(args)
    else:
        raise RuntimeError(f"Unsupported mode '{mode}'.")

    monitor_processes(processes)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
