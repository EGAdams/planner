# Repository Guidelines
Contributor quick-start for the hybrid Letta agents workspace. Keep changes small, documented, and runnable against the local Letta stack (port 8283).

## Project Structure & Module Organization
- `agents/` – orchestration samples (`hybrid_letta__claude_sdk.py`), connectivity smoke tests, and the partial `start_letta.sh` bootstrap.
- `memory_bridge/` – CLI for syncing and inspecting Letta memory blocks; uses `rich` for output.
- `tests/` – Python integration checks for the Letta server/database plus a Playwright dashboard probe (`test_letta_status.js`).
- Root utilities – `debug_letta_server.py`, `debug_letta_config.py`, `init_letta_db.py`, `letta_voice_agent.py`, and `openapi_letta.json`.

## Setup, Build, and Run
- Activate `/home/adamsl/planner/.venv/bin/activate` (or `python -m venv .venv && source .venv/bin/activate`), then `pip install letta_client requests rich python-dotenv livekit-agents playwright`.
- Start the backend: `letta server` (or `python debug_letta_server.py` for verbose output). Initialize Postgres via `python init_letta_db.py` (uses `LETTA_PG_URI`).
- Exercise orchestration samples with `python agents/hybrid_letta__claude_sdk.py` or `python agents/test_letta_minimal.py`.
- Memory bridge examples: `python memory_bridge/main.py list`, `python memory_bridge/main.py sync --project planner`.
- Voice pipeline: `python letta_voice_agent.py` (requires LiveKit/OpenAI/Deepgram/Cartesia keys).

## Testing Guidelines
- Run `pytest tests`; several tests expect the Letta server on `http://localhost:8283` and a populated `~/.letta/letta.db`. Start services first.
- Targeted runs: `python tests/test_letta_server.py` (health), `python tests/test_letta_db_init.py` (tables), `python tests/test_letta_memory.py` (memory flows).
- Dashboard probe: `node tests/test_letta_status.js` after installing Playwright; update the HTML path if needed. Attach `/tmp/letta_dashboard_status.png` for UI-related PRs.
- Add focused tests with clear prereqs; keep integration output concise.

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indents, type hints where practical, docstrings for scripts/CLI entry points, and f-strings. Module/file names snake_case; classes PascalCase; env/config constants uppercase.
- JavaScript helpers use CommonJS (`require`). Match the current style unless migrating intentionally.
- Configuration flows through `.env` (via `python-dotenv`) and environment variables rather than hardcoding.

## Commit & Pull Request Guidelines
- Use concise, present-tense commits similar to existing history (e.g., `add hybrid letta claude sdk agent`). Squash only when it clarifies the narrative.
- PRs should include what changed, how to run it (commands + required services/ports), test output or screenshots when UI is touched, and linked issues/tasks if applicable.
- Avoid committing secrets or large log dumps; keep `.venv`, `.env`, and runtime artifacts out of version control.
