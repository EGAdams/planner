import os
import shlex
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

# ----------------------------
# Config (set via env vars)
# ----------------------------
# Only allow actions inside this directory tree.
WORKSPACE_ROOT = Path(os.environ.get("EXECUTOR_WORKSPACE_ROOT", str(Path.cwd()))).resolve()

# Simple bearer token auth (required). Set this env var.
EXECUTOR_TOKEN = os.environ.get("EXECUTOR_TOKEN", "")

# Optional: restrict commands to an allowlist (recommended).
# If empty, commands are allowed but still run inside WORKSPACE_ROOT.
# Example: "python,python3,pytest,git,node,npm"
ALLOW_CMDS_RAW = os.environ.get("EXECUTOR_ALLOW_CMDS", "").strip()
ALLOW_CMDS = {c.strip() for c in ALLOW_CMDS_RAW.split(",") if c.strip()}

# Safety: block obviously dangerous commands even if allowlist is empty.
BLOCKED_PREFIXES = (
    "rm", "del", "rmdir", "format", "mkfs", "shutdown", "reboot", "poweroff",
    "diskpart", "bcdedit", "reg", "sc", "net", "wmic"
)

app = FastAPI(title="Local Executor", version="1.0.0")


def _require_auth(auth_header: Optional[str]) -> None:
    if not EXECUTOR_TOKEN:
        raise HTTPException(status_code=500, detail="Server misconfigured: EXECUTOR_TOKEN not set")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing/invalid Authorization header")
    token = auth_header.split(" ", 1)[1].strip()
    if token != EXECUTOR_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


def _safe_resolve_path(relative_path: str) -> Path:
    # Normalize and force under WORKSPACE_ROOT
    p = (WORKSPACE_ROOT / relative_path).resolve()
    if WORKSPACE_ROOT not in p.parents and p != WORKSPACE_ROOT:
        raise HTTPException(status_code=400, detail=f"Path escapes workspace root: {relative_path}")
    return p


def _check_command_allowed(cmd: List[str]) -> None:
    if not cmd:
        raise HTTPException(status_code=400, detail="Empty command")
    first = cmd[0].lower()

    if first in BLOCKED_PREFIXES:
        raise HTTPException(status_code=400, detail=f"Command blocked for safety: {first}")

    if ALLOW_CMDS and first not in {c.lower() for c in ALLOW_CMDS}:
        raise HTTPException(status_code=400, detail=f"Command not in allowlist: {first}")


class RunRequest(BaseModel):
    command: str                 # e.g. "pytest -q"
    cwd: str = "."               # relative to workspace root
    timeout_sec: int = 60
    env: Optional[Dict[str, str]] = None


class RunResponse(BaseModel):
    returncode: int
    stdout: str
    stderr: str
    cwd_resolved: str


class ReadRequest(BaseModel):
    path: str                    # relative to workspace root
    max_bytes: int = 200_000


class ReadResponse(BaseModel):
    path_resolved: str
    content: str


class WriteRequest(BaseModel):
    path: str                    # relative to workspace root
    content: str
    create_dirs: bool = True
    overwrite: bool = True


class WriteResponse(BaseModel):
    path_resolved: str
    bytes_written: int


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "workspace_root": str(WORKSPACE_ROOT),
        "allow_cmds": sorted(list(ALLOW_CMDS)),
    }


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest, authorization: Optional[str] = Header(default=None)) -> RunResponse:
    _require_auth(authorization)

    cwd_raw = (req.cwd or ".").strip()
    if cwd_raw in ("", "."):
        cwd_path = WORKSPACE_ROOT
    else:
        cwd_path = _safe_resolve_path(cwd_raw)

    if not cwd_path.exists() or not cwd_path.is_dir():
        raise HTTPException(status_code=400, detail=f"cwd does not exist or is not a directory: {req.cwd}")


    cmd_list = shlex.split(req.command)
    _check_command_allowed(cmd_list)

    env = os.environ.copy()
    if req.env:
        env.update(req.env)

    try:
        p = subprocess.run(
            cmd_list,
            cwd=str(cwd_path),
            env=env,
            capture_output=True,
            text=True,
            timeout=max(1, int(req.timeout_sec)),
            shell=False,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail=f"Command timed out after {req.timeout_sec}s")
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=f"Command not found: {cmd_list[0]}")

    return RunResponse(
        returncode=p.returncode,
        stdout=p.stdout[-200_000:],
        stderr=p.stderr[-200_000:],
        cwd_resolved=str(cwd_path),
    )


@app.post("/read", response_model=ReadResponse)
def read(req: ReadRequest, authorization: Optional[str] = Header(default=None)) -> ReadResponse:
    _require_auth(authorization)

    path = _safe_resolve_path(req.path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {req.path}")

    data = path.read_bytes()
    data = data[: max(1, int(req.max_bytes))]
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        # Fall back to latin-1 to avoid crashing; still safe for text-ish files.
        content = data.decode("latin-1")

    return ReadResponse(path_resolved=str(path), content=content)


@app.post("/write", response_model=WriteResponse)
def write(req: WriteRequest, authorization: Optional[str] = Header(default=None)) -> WriteResponse:
    _require_auth(authorization)

    path = _safe_resolve_path(req.path)

    if path.exists() and not req.overwrite:
        raise HTTPException(status_code=409, detail=f"File exists and overwrite=false: {req.path}")

    if req.create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(req.content, encoding="utf-8")

    return WriteResponse(path_resolved=str(path), bytes_written=len(req.content.encode("utf-8")))
