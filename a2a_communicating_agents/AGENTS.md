# Repository Guidelines

## Project Structure & Module Organization
- `agent_messaging/`: transports, `messenger.py`, and fixtures under `agent_messaging/tests/`.
- `orchestrator_agent/`: routing brain via `main.py`; posts jobs through the messaging hub.
- `dashboard_agent/`: reliability bot that keeps the Node dashboard up via HTTP probes and runtime artifacts.
- `hybrid_letta_agents/`: Letta experimentation (memory bridge, voice, vitest config, docs) plus `tests/` for the Letta SDK.
- `tests/`: Agent A/B chat walkthroughs for manual smoke tests; startup helpers like `start_a2a_system.sh` live at the root.

## Build, Test, and Development Commands
- `source ../.venv/bin/activate` — reuse the shared virtualenv; pull Letta extras with `pip install -r hybrid_letta_agents/requirements.txt`.
- `./start_a2a_system.sh` — boots Letta memory, orchestrator, dashboard agent, and the admin UI (logs go to `../logs/`).
- `python agent_messaging/run_collective.py` — quick discovery + delegation smoke test.
- `python -m pytest agent_messaging/tests/test_memory_system.py -q`, `pytest hybrid_letta_agents/tests -q`, plus the paired `python tests/test_agent_a.py` / `python tests/test_agent_b.py` runs form the baseline suite.

## Coding Style & Naming Conventions
Target Python 3.11+, PEP 8 formatting (4-space indents, snake_case functions, UpperCamelCase classes), and type hints similar to the current agents. File-level constants stay in ALL_CAPS (see `AGENT_NAME`). Prefer `pathlib.Path` and the existing logging helpers over ad-hoc prints. Inside `hybrid_letta_agents`, keep ES module syntax, two-space indents, and run files through the Vitest tooling in `vitest.config.js`. Name tests descriptively (`test_memory_system.py`, `test_letta_status.js`) and avoid committing generated data under `storage/` or `logs/`.

## Testing Guidelines
Changes affecting transports, routing, or Letta bridges need automated coverage via `pytest -q` and, for JS diagnostics, `npx vitest run`. When modifying orchestrator or dashboard flows, capture transcripts or runbooks under `agent_messaging/tests/` or `hybrid_letta_agents/agents/*.md` so automation can replay them. Manual Agent A/B chat runs should be documented in the PR body along with log snippets from `../logs/`.

## Commit & Pull Request Guidelines
Recent commits show short imperative summaries such as `add letta.log to git ignore` and `Fixed parse bank statement verify…`. Keep that pattern, optionally prefixing the subsystem (`agent_messaging:`) and referencing Task Master IDs or GitHub issues in the body. Pull requests must describe the problem, commands run, and any UI impact (screenshots for dashboard tweaks). Include rollback notes (`./stop_a2a_system.sh`) and keep refactors isolated.

## Configuration & Security Notes
Secrets stay in the workspace-level `.env`; never add keys, Chromadb dumps, or log archives to Git. Use `update_config.py` or Task Master commands rather than editing generated config files, and document any new config or dependency (including standard ports 8283/3000) in the nearest README.
