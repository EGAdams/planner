#!/usr/bin/env python3
"""
hybrid_letta__codex_sdk.py

Letta Orchestrator agent + Codex CLI-backed Coder & Tester tools.

- Letta runs as the orchestrator with long-term memory.
- The Coder & Tester are implemented as custom tools that call the Codex CLI SDK so
  the entire agent team runs on the same OpenAI model as the orchestrator.
- The orchestrator "sees" all messages, tool calls, and tool returns and can store
  specs, code, and tests in its memory blocks.

Requirements (host + Letta tool sandbox):

  pip install letta-client
  npm install -g @openai/codex   # provides the Codex CLI + SDK

Environment:

  LETTA_BASE_URL      # e.g. http://localhost:8283  (optional, defaults to that)
  OPENAI_API_KEY      # used by Letta server for openai/gpt-4o-mini
  CODEX_MODEL         # optional override for Codex CLI model (defaults to gpt-5.1-codex if ORCH_MODEL unsupported)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
import textwrap
from typing import Any, Dict, List, Optional, Tuple

import letta_client
from letta_client import Letta


# ---------- Configuration ----------

# Where generated code / tests will be written on the host
WORKSPACE_DIR = Path(__file__).resolve().parent
CONTRACT_LOG_NAME = "tdd_contracts.jsonl"

# Orchestrator model inside Letta (Letta only supports: letta, openai, google_ai)
ORCH_MODEL = os.environ.get("ORCH_MODEL", "openai/gpt-4o-mini")

# Initial task given to the orchestrator
FEATURE_SPEC = textwrap.dedent(
    """
    Build a Python helper called `add(a: int, b: int) -> int` that returns the sum of two integers.
    Validate type handling (raise `TypeError` for non-ints) and cover positive, negative, zero,
    and large-number scenarios.
    """
).strip()

USER_TASK = textwrap.dedent(
    f"""
    You are the Orchestrator Agent for a Codex-based TDD trio (Coder + Tester + Pytest runner).

    **Specification**
    {FEATURE_SPEC}

    **Strict workflow (no skipping steps):**
    1. Use the Tester Tool *first* to generate pytest tests from the specification. Pass the spec via the
       `spec` argument and leave `implementation` empty until code exists. Write tests to
       `test_add.py` inside the provided workspace directory.
    2. Immediately run the Pytest Runner Tool with `target` pointing to the new test file and set
       `expect_failure=True`. Capture the failure reason in your notes.
    3. After seeing the red test, call the Coder Tool to implement the function in `add.py`. Keep the
       implementation minimal but correct.
    4. Run the Pytest Runner Tool again with `expect_failure=False` to ensure the tests now pass.
    5. Accumulate the JSON contracts returned by each tool call (test generation, red test run, code
       generation, green test run) and pass them to the Validator Tool as a JSON array string via the
       `contracts_json` argument. Do not skip this step.
    6. Summarize the cycle: mention file paths, how the first test run failed, how the second passed,
       and the validator result.

    **Tool usage reminders**
    - Always pass the literal spec text above into both the Tester and Coder so they have context.
    - When calling the Tester Tool after code exists, pass both the spec and the latest implementation.
    - The workspace directory path is surfaced via the `workspace_dir` argument; use it consistently so
      all files land inside the shared location.
    - Each tool returns a JSON contract describing its work—inspect these contracts to keep the team
      honest and reference them in your summary.
    - Use the generalized Test Runner Tool to execute pytest, node-based suites, or any command the
      project requires. Always set `framework` and `expect_failure` appropriately so the contracts are
      accurate.
    - When calling the Validator Tool, either pass a JSON array string of prior contracts, concatenate
      the raw JSON contracts with whitespace, or simply reference the shared `tdd_contracts.jsonl`
      file in the workspace—the validator can parse any of these formats.

    Follow this red-green-refactor loop every time; do not mark the task complete unless the green run
    succeeds.
    """
).strip()
# ---------- Tool implementations (executed inside Letta) ----------
def _evaluate_contracts(contracts: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, Any]]:
    errors: List[str] = []

    test_gen = next(
        (c for c in contracts if c.get("contract_type") == "test_generation"),
        None,
    )
    if not test_gen:
        errors.append("Missing test_generation contract.")

    red_run = next(
        (
            c
            for c in contracts
            if c.get("contract_type") == "test_run" and c.get("expect_failure")
        ),
        None,
    )
    if not red_run:
        errors.append("Missing red-phase test run (expect_failure=True).")
    elif red_run.get("passed"):
        errors.append("Red-phase test run unexpectedly passed.")

    code_gen = next(
        (c for c in contracts if c.get("contract_type") == "code_generation"),
        None,
    )
    if not code_gen:
        errors.append("Missing code_generation contract after red phase.")

    green_run = next(
        (
            c
            for c in contracts
            if c.get("contract_type") == "test_run" and not c.get("expect_failure")
        ),
        None,
    )
    if not green_run:
        errors.append("Missing green-phase test run (expect_failure=False).")
    elif not green_run.get("passed"):
        errors.append("Green-phase test run failed.")

    if all([test_gen, red_run, code_gen, green_run]):
        if not (test_gen["_order"] < red_run["_order"] < code_gen["_order"] < green_run["_order"]):
            errors.append("Tool execution order does not follow test->red->code->green sequence.")

        for label, entry in ("tests", test_gen), ("code", code_gen):
            path = entry.get("file_path")
            if path and not Path(path).exists():
                errors.append(f"{label.title()} file missing on disk: {path}")

    summary = {
        "tests_file": test_gen.get("file_path") if test_gen else None,
        "code_file": code_gen.get("file_path") if code_gen else None,
        "red_target": red_run.get("target") if red_run else None,
        "green_target": green_run.get("target") if green_run else None,
    }
    return errors, summary

def run_codex_coder(
    spec: str,
    language: str = "python",
    file_name: str = "generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Codex Coder Agent.

    Args:
        spec: Natural-language spec for the feature to implement.
        language: Target programming language (e.g. "python", "typescript").
        file_name: File name to write the generated code into.
        workspace_dir: Optional workspace directory to write into. If not provided,
            defaults to the current working directory of the tool.

    Returns:
        A short status string including the file path where code was written.
    """
    import json
    import hashlib
    import os
    import shutil
    import subprocess
    import sys
    import textwrap
    from pathlib import Path

    prompt = textwrap.dedent(
        f"""
        <instructions>
        Instructions:
        You are an elite software engineer (Coder Agent).
        Implement the requested feature as a single {language} file.
        Return ONLY the raw file contents without fences or commentary.
        </instructions>

        <spec>
        Specification:
        ---------------- SPEC START ----------------
        {spec}
        ----------------- SPEC END -----------------
        </spec>
        """
    )

    auth_path = Path.home() / ".codex" / "auth.json"
    if not auth_path.exists():
        raise RuntimeError(
            f"Codex credentials not found at {auth_path}. "
            "Run `codex login` or `codex auth --with-api-key` first."
        )

    codex_bin = shutil.which("codex")
    if not codex_bin:
        raise RuntimeError("Codex CLI binary not found on PATH. Install via `npm install -g @openai/codex`.")

    model_name = os.environ.get("CODEX_MODEL")
    print( "CODEX_MODEL:", model_name )
    if not model_name:
        orch_model = os.environ.get("ORCH_MODEL", "")
        candidate = orch_model.split("/", 1)[-1] if "/" in orch_model else orch_model
        print( "ORCH_MODEL:", orch_model, "candidate:", candidate )
        if candidate and not candidate.startswith("gpt-4o"):
            print( "setting model_name to candidate:", candidate )
            model_name = candidate
        else:
            print( "setting model_name to gpt-5.1-codex because candidate was:", candidate )
            model_name = "gpt-5.1-codex"

    base_dir = Path(workspace_dir or os.getcwd())
    base_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        codex_bin,
        "exec",
        "--experimental-json",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
    ]
    if model_name:
        cmd.extend(["--model", model_name])

    completed = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        cwd=str(base_dir),
        check=False,
    )

    final_text: Optional[str] = None
    failure_reason: Optional[str] = None

    for raw_line in completed.stdout.splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        etype = event.get("type")
        if etype == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                final_text = item.get("text", "")
        elif etype == "turn.failed":
            error = event.get("error", {}) or {}
            failure_reason = error.get("message") or str(error)

    if completed.returncode != 0:
        raise RuntimeError(
            f"Codex CLI failed with exit code {completed.returncode}: {completed.stderr.strip()}"
        )

    if failure_reason:
        raise RuntimeError(f"Codex CLI reported failure: {failure_reason}")

    if final_text is None or not final_text.strip():
        raise RuntimeError("Codex CLI returned empty response.")

    code_text = final_text.strip()

    if not code_text.strip():
        raise RuntimeError("Coder tool returned empty content.")

    # Best-effort strip surrounding fences if the model returned ``` blocks
    if "```" in code_text:
        segments = code_text.split("```")
        if len(segments) >= 3:
            # content is usually in the 2nd segment
            code_text = segments[1]
            # strip possible "python" language tag on the first line
            lines = code_text.splitlines()
            if lines and lines[0].strip().startswith(("python", "py")): # TODO: extend for other languages # use language param?
                lines = lines[1:]
            code_text = "\n".join(lines)

    # Write to file
    base_dir = Path(workspace_dir or os.getcwd())
    base_dir.mkdir(parents=True, exist_ok=True)
    out_path = base_dir / file_name
    out_path.write_text(code_text, encoding="utf-8")

    contract = {
        "contract_type": "code_generation",
        "status": "success",
        "file_path": str(out_path),
        "language": language,
        "bytes": len(code_text.encode("utf-8")),
        "lines": len(code_text.splitlines()),
        "spec_hash": hashlib.sha256(spec.encode("utf-8")).hexdigest(),
    }
    try:
        default_log_name = CONTRACT_LOG_NAME
    except NameError:
        default_log_name = "tdd_contracts.jsonl"
    log_name = os.environ.get("CONTRACT_LOG_NAME", default_log_name)
    log_path = base_dir / log_name
    try:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(contract) + "\n")
    except OSError:
        pass
    return json.dumps(contract, indent=2)


def run_codex_tester(
    spec: str,
    implementation: str = "",
    language: str = "python",
    test_framework: str = "pytest",
    file_name: str = "test_generated_code.py",
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Codex Tester Agent.

    Args:
        spec: Natural-language feature specification that tests should target.
        implementation: Optional current implementation snippet to give the tester
            concrete references once code exists.
        language: Programming language of the code.
        test_framework: e.g. "pytest", "unittest", "jest".
        file_name: File name to write the generated tests into.
        workspace_dir: Optional workspace directory to write into. If not provided,
            defaults to the current working directory of the tool.

    Returns:
        A short status string including the file path where tests were written.
    """
    import json
    import hashlib
    import os
    import shutil
    import subprocess
    import textwrap
    from pathlib import Path

    prompt = textwrap.dedent(
        f"""
        You are an elite software test engineer (Tester Agent).
        Given the feature specification (and optional current implementation), produce a comprehensive
        {test_framework} test suite in {language}. Cover happy paths, edge cases, and failure handling.
        Return ONLY the raw test file contents without fences or commentary.

        Feature spec:
        --------------- SPEC START ---------------
        {spec}
        ---------------- SPEC END ----------------

        Current implementation (may be empty when tests are written first):
        --------- IMPLEMENTATION START ---------
        {implementation}
        ---------- IMPLEMENTATION END ----------
        """
    )

    auth_path = Path.home() / ".codex" / "auth.json"
    if not auth_path.exists():
        raise RuntimeError(
            f"Codex credentials not found at {auth_path}. "
            "Run `codex login` or `codex auth --with-api-key` first."
        )

    codex_bin = shutil.which("codex")
    if not codex_bin:
        raise RuntimeError("Codex CLI binary not found on PATH. Install via `npm install -g @openai/codex`.")

    model_name = os.environ.get("CODEX_MODEL")
    if not model_name:
        orch_model = os.environ.get("ORCH_MODEL", "")
        candidate = orch_model.split("/", 1)[-1] if "/" in orch_model else orch_model
        if candidate and not candidate.startswith("gpt-4o"):
            model_name = candidate
        else:
            model_name = "gpt-5.1-codex"

    base_dir = Path(workspace_dir or os.getcwd())
    base_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        codex_bin,
        "exec",
        "--experimental-json",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
    ]
    if model_name:
        cmd.extend(["--model", model_name])

    completed = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        cwd=str(base_dir),
        check=False,
    )

    final_text: Optional[str] = None
    failure_reason: Optional[str] = None

    for raw_line in completed.stdout.splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        etype = event.get("type")
        if etype == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                final_text = item.get("text", "")
        elif etype == "turn.failed":
            error = event.get("error", {}) or {}
            failure_reason = error.get("message") or str(error)

    if completed.returncode != 0:
        raise RuntimeError(
            f"Codex CLI failed with exit code {completed.returncode}: {completed.stderr.strip()}"
        )

    if failure_reason:
        raise RuntimeError(f"Codex CLI reported failure: {failure_reason}")

    if final_text is None or not final_text.strip():
        raise RuntimeError("Codex CLI returned empty response.")

    test_text = final_text.strip()

    if not test_text.strip():
        raise RuntimeError("Tester tool returned empty content.")

    # Best-effort strip ``` fences
    if "```" in test_text:
        segments = test_text.split("```")
        if len(segments) >= 3:
            test_text = segments[1]
            lines = test_text.splitlines()
            if lines and lines[0].strip().startswith(("python", "py")):
                lines = lines[1:]
            test_text = "\n".join(lines)

    base_dir = Path(workspace_dir or os.getcwd())
    base_dir.mkdir(parents=True, exist_ok=True)
    out_path = base_dir / file_name
    out_path.write_text(test_text, encoding="utf-8")

    contract = {
        "contract_type": "test_generation",
        "status": "success",
        "file_path": str(out_path),
        "test_framework": test_framework,
        "language": language,
        "spec_hash": hashlib.sha256(spec.encode("utf-8")).hexdigest(),
        "implementation_hash": hashlib.sha256((implementation or "").encode("utf-8")).hexdigest(),
    }
    try:
        default_log_name = CONTRACT_LOG_NAME
    except NameError:
        default_log_name = "tdd_contracts.jsonl"
    log_name = os.environ.get("CONTRACT_LOG_NAME", default_log_name)
    log_path = base_dir / log_name
    try:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(contract) + "\n")
    except OSError:
        pass
    return json.dumps(contract, indent=2)


def run_test_suite(
    framework: str = "pytest",
    target: str = "tests",
    workspace_dir: Optional[str] = None,
    expect_failure: bool = False,
    extra_args: str = "",
    command_override: Optional[str] = None,
) -> str:
    """
    Execute a test command (pytest, node, custom) and enforce TDD expectations.

    Args:
        framework: Logical framework name ("pytest", "vitest", "custom", etc.).
        target: Path or pattern passed to the runner (file, directory, glob).
        workspace_dir: Optional workspace directory override; defaults to tool cwd.
        expect_failure: Whether this run is meant to fail (red phase) or pass (green phase).
        extra_args: Additional CLI args, space-delimited.
        command_override: Optional full command string to execute instead of the default
            framework-specific command.
    """
    import json
    import shlex
    import subprocess
    import sys
    from pathlib import Path
    import os

    base_dir = Path(workspace_dir or Path.cwd())
    base_dir.mkdir(parents=True, exist_ok=True)

    if command_override:
        cmd = shlex.split(command_override)
    elif framework.lower() == "pytest":
        cmd = [sys.executable, "-m", "pytest", target]
    elif framework.lower() == "vitest":
        cmd = ["npx", "vitest", "run", target]
    else:
        raise RuntimeError(
            f"Framework '{framework}' requires command_override to be set for execution."
        )

    if extra_args.strip():
        cmd.extend(shlex.split(extra_args))

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(base_dir),
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Failed to execute test command {cmd}: {exc}")

    output = proc.stdout + "\n" + proc.stderr
    passed = proc.returncode == 0

    if expect_failure and passed:
        raise RuntimeError(
            f"{framework} tests unexpectedly passed while expect_failure=True. Output:\n" + output
        )
    if not expect_failure and not passed:
        raise RuntimeError(
            f"{framework} tests failed but expect_failure=False. Output:\n" + output
        )

    contract = {
        "contract_type": "test_run",
        "status": "success",
        "framework": framework,
        "target": target,
        "command": " ".join(cmd),
        "expect_failure": expect_failure,
        "passed": passed,
        "exit_code": proc.returncode,
        "outcome": "failed_as_expected" if expect_failure else "passed",
        "output": output.strip(),
    }
    try:
        default_log_name = CONTRACT_LOG_NAME
    except NameError:
        default_log_name = "tdd_contracts.jsonl"
    log_name = os.environ.get("CONTRACT_LOG_NAME", default_log_name)
    log_path = base_dir / log_name
    try:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(contract) + "\n")
    except OSError:
        pass
    return json.dumps(contract, indent=2)


def run_tdd_validator(
    contracts_json: str,
    workspace_dir: Optional[str] = None,
) -> str:
    """
    Validate the RED→GREEN workflow by inspecting prior tool contracts.

    Args:
        contracts_json: JSON array string of previously returned tool contracts in chronological order.
        workspace_dir: Optional workspace directory reference for reporting.
    """
    import json
    from pathlib import Path

    raw = contracts_json.strip()
    if not raw:
        raise RuntimeError("contracts_json cannot be empty")

    decoder = json.JSONDecoder()
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("not a list")
    except Exception:
        data = []
        idx = 0
        length = len(raw)
        try:
            while idx < length:
                while idx < length and raw[idx].isspace():
                    idx += 1
                if idx >= length:
                    break
                obj, next_idx = decoder.raw_decode(raw, idx)
                data.append(obj)
                idx = next_idx
        except json.JSONDecodeError:
            data = []

    if not data and workspace_dir:
        try:
            default_log_name = CONTRACT_LOG_NAME
        except NameError:
            default_log_name = "tdd_contracts.jsonl"
        log_path = Path(workspace_dir) / default_log_name
        if log_path.exists():
            for line in log_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not data:
        raise RuntimeError("No contract entries provided to validator")

    contracts: List[Dict[str, Any]] = []
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise RuntimeError("Each contract entry must be a JSON object")
        entry = dict(entry)
        entry.setdefault("_order", idx)
        contracts.append(entry)

    errors: List[str] = []

    test_gen = next(
        (c for c in contracts if c.get("contract_type") == "test_generation"),
        None,
    )
    if not test_gen:
        errors.append("Missing test_generation contract.")

    red_run = next(
        (
            c
            for c in contracts
            if c.get("contract_type") == "test_run" and c.get("expect_failure")
        ),
        None,
    )
    if not red_run:
        errors.append("Missing red-phase test run (expect_failure=True).")
    elif red_run.get("passed"):
        errors.append("Red-phase test run unexpectedly passed.")

    code_gen = next(
        (c for c in contracts if c.get("contract_type") == "code_generation"),
        None,
    )
    if not code_gen:
        errors.append("Missing code_generation contract after red phase.")

    green_run = next(
        (
            c
            for c in contracts
            if c.get("contract_type") == "test_run" and not c.get("expect_failure")
        ),
        None,
    )
    if not green_run:
        errors.append("Missing green-phase test run (expect_failure=False).")
    elif not green_run.get("passed"):
        errors.append("Green-phase test run failed.")

    if all([test_gen, red_run, code_gen, green_run]):
        if not (test_gen["_order"] < red_run["_order"] < code_gen["_order"] < green_run["_order"]):
            errors.append("Tool execution order does not follow test->red->code->green sequence.")

        for label, entry in ("tests", test_gen), ("code", code_gen):
            path = entry.get("file_path")
            if path and not Path(path).exists():
                errors.append(f"{label.title()} file missing on disk: {path}")

    summary = {
        "tests_file": test_gen.get("file_path") if test_gen else None,
        "code_file": code_gen.get("file_path") if code_gen else None,
        "red_target": red_run.get("target") if red_run else None,
        "green_target": green_run.get("target") if green_run else None,
    }
    if errors:
        raise RuntimeError("; ".join(errors))

    summary_contract = {
        "contract_type": "tdd_validation",
        "status": "success",
        "workspace_dir": workspace_dir,
        **summary,
    }
    return json.dumps(summary_contract, indent=2)


def create_letta_client() -> Letta:
    base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
    print(f"Using self-hosted Letta at {base_url} (override with LETTA_BASE_URL).")
    client = Letta(base_url=base_url)
    print(f"Letta client created with base URL: {client.base_url}")
    return client


def ensure_workspace_dir() -> None:
    print(f"WORKSPACE_DIR = {WORKSPACE_DIR}")
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def reset_contract_log() -> None:
    log_path = WORKSPACE_DIR / CONTRACT_LOG_NAME
    if log_path.exists():
        log_path.unlink()


def _extract_tool_return_text(tool_return: Any) -> str:
    if tool_return is None:
        return ""
    if isinstance(tool_return, str):
        return tool_return
    content = getattr(tool_return, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        if parts:
            return "\n".join(parts)
    text = getattr(tool_return, "text", None)
    if isinstance(text, str):
        return text
    return str(tool_return)


def validate_tdd_contracts(messages: List[Any]) -> None:
    contracts: List[Dict[str, Any]] = []
    for msg in messages:
        if getattr(msg, "message_type", "") != "tool_return_message":
            continue
        payload_text = _extract_tool_return_text(getattr(msg, "tool_return", None))
        if not payload_text:
            continue
        try:
            data = json.loads(payload_text)
        except json.JSONDecodeError:
            continue
        data["_order"] = len(contracts)
        contracts.append(data)

    errors, summary = _evaluate_contracts(contracts)
    if errors:
        raise RuntimeError("\n".join(["TDD contract validation failed:"] + [f"- {e}" for e in errors]))

    print("\n✅ Inline TDD contract validation passed.")
    print(f"  - Tests file: {summary.get('tests_file')}")
    print(f"  - Pytest red run target: {summary.get('red_target')}")
    print(f"  - Code file: {summary.get('code_file')}")
    print(f"  - Pytest green run target: {summary.get('green_target')}")


# ---------- Main orchestration ----------

def main() -> None:
    print("Starting hybrid_letta__codex_sdk.py...")
    ensure_workspace_dir()
    reset_contract_log()

    client = create_letta_client()

    # 1) Register tools (once). If they already exist with the same signature,
    #    create_from_function will upsert them.
    coder_tool = client.tools.create_from_function(func=run_codex_coder)
    print("Created coder_tool:")
    print(f"  - ID:   {coder_tool.id}")
    print(f"  - Name: {coder_tool.name}")

    tester_tool = client.tools.create_from_function(func=run_codex_tester)
    print("Created tester_tool:")
    print(f"  - ID:   {tester_tool.id}")
    print(f"  - Name: {tester_tool.name}")

    test_runner_tool = client.tools.create_from_function(func=run_test_suite)
    print("Created test_runner_tool:")
    print(f"  - ID:   {test_runner_tool.id}")
    print(f"  - Name: {test_runner_tool.name}")

    validator_tool = client.tools.create_from_function(func=run_tdd_validator)
    print("Created validator_tool:")
    print(f"  - ID:   {validator_tool.id}")
    print(f"  - Name: {validator_tool.name}")

    # 2) Create an orchestrator agent which can call those tools
    print(f"Creating orchestrator with model: {ORCH_MODEL}")
    orchestrator_agent = client.agents.create(
        model=ORCH_MODEL,
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "role",
                "value": "You are an orchestrator who manages a Codex-based Coder and Tester.",
                "limit": 2000,
            },
            {
                "label": "workspace",
                "value": f"Workspace directory on the host is: {WORKSPACE_DIR}",
                "limit": 2000,
            },
        ],
        tools=[
            coder_tool.name,
            tester_tool.name,
            test_runner_tool.name,
            validator_tool.name,
        ],
        # tool_exec_environment_variables are available as os.getenv(...) inside tools
        tool_exec_environment_variables={
            "ORCH_MODEL": ORCH_MODEL,
            "WORKSPACE_DIR": str(WORKSPACE_DIR),
            "CODEX_MODEL": os.environ.get("CODEX_MODEL", ""),
        },
    )

    print(f"Created orchestrator agent: {orchestrator_agent.id}")

    # 3) Send initial high-level task to orchestrator
    print("Sending initial task to orchestrator...")
    try:
        response = client.agents.messages.create(
            agent_id=orchestrator_agent.id,
            messages=[{"role": "user", "content": USER_TASK}],
            timeout=180,
        )
    except letta_client.APIConnectionError as e:
        print("❌ Letta connection / timeout error while sending message.")
        print(repr(e))
        print(
            "\nHints:\n"
            "- Make sure your Letta server is running and reachable at LETTA_BASE_URL.\n"
            "- Confirm the server has OPENAI_API_KEY set so it can call openai/gpt-4o-mini.\n"
            "- Confirm the Codex CLI is installed + authenticated via `codex login` so the tools can call Codex.\n"
            "- If the operation is legitimately long-running, you can increase "
            "timeout_in_seconds further."
        )
        return

    # 4) Print orchestrator messages (including tool calls / returns)
    print("\n=== Orchestrator response ===\n")
    for msg in response.messages:
        mtype = getattr(msg, "message_type", None)
        if mtype == "assistant_message":
            print(f"[assistant] {msg.content}")
        elif mtype == "user_message":
            print(f"[user] {msg.content}")
        elif mtype == "reasoning_message":
            print(f"[reasoning] {msg.reasoning}")
        elif mtype == "tool_call_message":
            print(f"[tool-call] {msg.tool_call.name} args={msg.tool_call.arguments}")
        elif mtype == "tool_return_message":
            print(f"[tool-return] {msg.tool_return}")
        else:
            # Fallback for older SDK versions
            print(msg)

    validate_tdd_contracts(response.messages)

    print("\nDone. Check the workspace directory for generated files:")
    print(f"  {WORKSPACE_DIR}")


if __name__ == "__main__":
    main()
