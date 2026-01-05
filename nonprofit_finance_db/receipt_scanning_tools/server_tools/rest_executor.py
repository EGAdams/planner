import json
import urllib.request
import urllib.error

#
# This is not used here, it is used by the Letta Server Agents
# It is listed here for version control convenience.
#

def rest_executor(command: str, cwd: str = ".", timeout_sec: int = 60) -> dict:
    # Fix common ADE/user formatting like: "command: python3 -c ..."
    cmd = command.strip()
    if cmd.lower().startswith("command:"):
        cmd = cmd.split(":", 1)[1].strip()

    url = "http://10.0.0.7:8787/run"
    token = "6c9f1e4b5a2d8f7c0b3e9a4d7f2c1e8"

    payload = {
        "command": cmd,
        "cwd": cwd,
        "timeout_sec": int(timeout_sec),
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=int(timeout_sec) + 10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body)
        except Exception:
            detail = body
        raise RuntimeError(f"Executor HTTP {e.code}: {detail}") from e
