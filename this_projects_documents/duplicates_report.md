# Duplicate Markdown Report (content-identical files)

Generated via SHA-256 hashing of `.md` files (excluding `.venv` and `node_modules`). Total scanned: 876. Duplicate groups: 177.

## High-value duplicates to consolidate first
- **CLAUDE.md**: root, nonprofit_finance_db, office-assistant (identical). Pick one canonical and reference it.
- **empty files**: `doc/memory/memory_standards.md`, `pinecone_chat_dave_s/GEMINI.md` (both 0 bytes) — delete or populate.
- **DB integration doc**: `doc/architecture/nonprofit_database_integration.md` == `nonprofit_finance_db/doc/setup/db_integration_instructions.md` — keep one.
- **Gemini collective configs** (DECISION/agents/hooks/quality/research) duplicated across `.gemini-collective` roots and dashboard/gemini_test_agent — choose canonical per org.
- **Gemini agents/commands/docs** under `.gemini/agents|commands|docs` duplicated between root and dashboard/gemini_test_agent — consolidate or symlink.
- **Taskmaster/Claude command docs**: many `.claude/commands/tm/...` duplicates across root, dashboard, nonprofit_finance_db, office-assistant — pick one set.
- **Taskmaster CLAUDE.md**: identical in root `.claude_taskmaster`, nonprofit_finance_db/.taskmaster, office-assistant/.taskmaster.
- **Backend README**: `backend/services/README.md` duplicated under dashboard/gemini_test_agent.
- **Office-assistant test-results**: duplicate `error-context.md` files (3179 bytes) in `test-results/tests-browser-navigation-*`.

## Next steps
- Decide canonical sources for each group above.
- Replace other copies with links/refs or remove them after updating references.
- Hidden `.claude*`, `.codex*`, `.gemini*`, `.taskmaster` config files may be used by tooling; consolidate carefully or leave as-is if tooling expects local copies.
