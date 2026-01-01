# Hybrid Letta + LiveKit Runbook

What broke, how it was fixed, and how to start the stack next time.

## Issues Seen and Fixes
- Letta 0.14.0 on Postgres used `INSERT OR IGNORE`, causing 500s. Fixed by upgrading to Letta 0.15.1 and patching the installed `letta/orm/message.py` to use `ON CONFLICT` for Postgres sequence initialization (reapply if the venv is rebuilt).
- Postgres mode requires the patched equality check (`==` not `is`) so the Postgres branch is taken. Added `start_letta_postgres.sh` in `agents/` to automatically reapply the patch, verify env vars, kill running servers, and start Letta against Postgres.
- Letta server returned 401 when listing OpenAI models because env vars were not loaded into the server process. Solution: start Letta after `source ~/planner/.env` so `OPENAI_API_KEY` is present.
- `letta_client` no longer returns `output_text`; `hybrid_letta__claude_sdk.py` now prints assistant messages directly.
- Separate environments: Letta runs in `~/planner/.venv`; LiveKit runs in `~/planner/livekit-venv`. Mixing them caused dependency warnings; keep them isolated.
- Default local Postgres (installed/initialized) credentials that work here: `postgresql+asyncpg://letta:letta@localhost:5432/letta`. The Postgres starter script will auto-fill this if no DB URI is set.
- Common crash cause: placeholder Postgres URIs like `user:pass@host:5432/dbname`. The Postgres starter script now guards against these and falls back to the working default.

## Required Environments and Ports
- Letta server: `~/planner/.venv`, env file `~/planner/.env`, listens on `localhost:8283`.
- LiveKit server: `~/planner/livekit-venv`, binary at `/home/adamsl/ottomator-agents/livekit-agent/livekit-server`, listens on `0.0.0.0:7880`.

## One-Command Startup
Run the helper script to check ports and start anything that is down:
```bash
./start_local_stack.sh
```
Postgres-focused startup (applies the ON CONFLICT patch and starts Letta on Postgres):
```bash
cd agents
source ../../../.venv/bin/activate
export OPENAI_API_KEY=sk-...               # required
# optional: override DB URI; defaults to postgresql+asyncpg://letta:letta@localhost:5432/letta
# export LETTA_PG_URI=postgresql+asyncpg://user:pass@host:5432/dbname
./start_letta_postgres.sh
```

## Manual Startup (if you prefer)
- LiveKit: `cd /home/adamsl/ottomator-agents/livekit-agent && source ~/planner/livekit-venv/bin/activate && ./livekit-server --dev --bind 0.0.0.0`
- Letta: `cd ~/planner && source .venv/bin/activate && source .env && letta server --port 8283`

## Quick Checks & Debug
- Verify Postgres is reachable with default creds: `PGPASSWORD=letta psql -U letta -h localhost -p 5432 -c "select current_database(), current_user"`.
- Verify Letta health: `curl http://localhost:8283/v1/health/` (expects 200 OK).
- If agent creation fails with `INSERT OR IGNORE` on Postgres, rerun `start_letta_postgres.sh` to reapply the `ON CONFLICT` patch or patch `.venv/lib/python3.12/site-packages/letta/orm/message.py` manually.
- If the server crashes on startup, check for placeholder DB URIs and ensure `OPENAI_API_KEY` is set in the same shell that starts Letta.

## Notes
- The Postgres sequence patch lives inside the venv at `.venv/lib/python3.12/site-packages/letta/orm/message.py`. If you reinstall/upgrade Letta and the bug returns, reapply the ON CONFLICT patch or move to a Letta release that contains the fix upstream.
- Logs and PIDs: `~/planner/logs/livekit-server.log|.pid`, `~/planner/logs/letta-server.log|.pid`.
