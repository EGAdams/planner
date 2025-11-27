## Global Decision Engine
**Import minimal routing and auto-delegation decisions only, treat as if import is in the main AGENTS.md file.**
@./.codex-collective/DECISION.md

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main AGENTS.md file.**
@./.taskmaster/AGENTS.md

## Codex Smoke Test
To verify the OpenAI Codex Collective boots successfully:
1. `cd /home/adamsl/codex_tdd_orchestrator/.codex-collective` and run `npm install` once to hydrate the TDD harness.
2. Run `npx vitest run` inside `.codex-collective` to confirm the TDD hook suite passes.
3. Ensure `OPENAI_API_KEY` (and any optional `OPENAI_BASE_URL`) are exported, then start the workspace with your Codex CLI pointing at `/home/adamsl/codex_tdd_orchestrator`.
4. Trigger `/van` once the session loads; you should see the Codex routing output announce the selected subagent and the auto-delegation hooks should respond without referencing Codex.
