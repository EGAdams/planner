# Voice Agent Manager Expert Playbook

These instructions describe how to operate the hybrid Letta voice stack with a bias toward *self-healing* agent management. Follow them whenever coordinating work in this repository.

## Mission
- Keep the localhost LiveKit/Letta voice surface always talking to the intended specialist (`Agent_66`) and auto-correct when it drifts.
- Detect, heal, and document voice-session failures before the user notices.
- Reduce the number of manual toggles the user has to remember; if a step can be scripted or verified automatically, do it.

## Guardrails
- Never kill or reset long-running services unless logs prove they are wedged; prefer targeted cleanup (room eviction, dispatch retries, agent reselection).
- Do not modify secrets, `.env`, or generated config by hand—use existing scripts (`start_voice_system.sh`, `clean_livekit_rooms.sh`, `update_voice_token.sh`) or Task Master instructions.
- Maintain ASCII formatting, four-space Python indents, and existing ES-module style in UI code. Add comments only where behavior is non-obvious (healing logic, health probes).

## Agent_66 Lock Enforcement (Dec 27, 2025)
- `voice-agent-selector.html` and `voice-agent-selector-debug.html` now auto-select and highlight `Agent_66`, disable every other card, and resend its ID after each reconnect; clicking any other agent simply reaffirms the lock and shows a warning pill.
- `letta_voice_agent_optimized.py` cross-checks every `agent_selection` payload against `VOICE_PRIMARY_AGENT_NAME` (defaults to `Agent_66`) and refuses to switch if the requested agent name differs, speaking a reminder that the voice surface is locked.
- Always confirm logs show `Sent agent selection: Agent_66` on the frontend and `🔄 Agent selection request: Agent_66` / `✅ Using Agent_66 with ID:` on the backend before attempting any diagnosis—if those strings disappear, investigate the selector and worker guardrails first.

## Core Responsibilities
1. **State Awareness**
   - Inspect running workers (`ps -ef | grep letta_voice_agent`) and logs (`tail -f /tmp/letta_voice_agent.log`) before changing anything.
   - Track which agent ID is live by grepping for `Using Agent_66` or `Agent selection request`.

2. **Self-Healing Automations**
   - Prefer scripts that already encode recovery (`restart_voice_system.sh`, `clean_livekit_rooms.sh`, `recover_voice_system.sh`).
   - When adding new logic, encapsulate it in reusable helpers (e.g., a Python health check under `room_health_monitor.py` or shell snippets under `scripts/`).
   - Ensure frontend fixes broadcast both `room_cleanup` and `agent_selection` messages so the worker can self-correct without human intervention.

3. **Verification**
   - Baseline: `./test_dispatch_flow.sh`, `python verify_agent_loading.py`, and `python tests/test_voice_response.py`.
   - For UI conditions, note console evidence (`Sent agent selection`, `Switching from old agent`) rather than screenshots unless required.
   - When diagnosing failures, capture exact log excerpts and remediation command(s).

4. **Documentation**
   - Update the most relevant *_SUMMARY.md or *_GUIDE.md file instead of scattering new docs. Summaries must state symptom → detection → automated fix.
   - Record any new recovery script in `ROOM_RECOVERY_GUIDE.md` or `VOICE_AGENT_ROOT_CAUSE_REPORT.md`.

## Workflow Checklist
1. **Before Work**
   - `source ../.venv/bin/activate`
   - `pip install -r requirements.txt` if dependencies changed.
   - Confirm services via `./test_dispatch_flow.sh`.

2. **During Work**
   - When editing backend Python, run focused pytest (`pytest tests -q` or component-specific files).
   - For frontend changes, open `http://localhost:9000/debug`, connect, and ensure logs show `Agent_66`.
   - If a failure occurs, attempt automated recovery, verify, then only escalate to manual restarts.

3. **After Work**
   - Run at least one smoke command verifying self-healing (e.g., reconnect twice while tailing logs to show automatic agent switches).
   - Document outcomes in the relevant report file and mention commands run for verification.

## Communication Style
- Be concise, reference concrete commands/log lines, and always include the “next automated step” so operators can reproduce healing actions quickly.
- When handing off, highlight outstanding risks, what monitors are watching them, and how they self-remediate.
