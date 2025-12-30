# Repository Guidelines

## Database Credentials
All database credentals are in this file:
```bash
/home/adamsl/planner/.env
```

## Virtual Environment Location
```bash
/home/adamsl/planner/.venv/
```

## Project Structure & Module Organization
- `app/` contains the core services: domain models under `models/`, persistence helpers in `repositories/`, and Postgres access wired in `app/db/`.
- `parsers/` implements `BaseParser`; extend it when adding CSV, PDF, or OFX importers so the ingestion pipeline can swap implementations cleanly.
- `detection/` owns duplicate matching logic (`matching_algorithms.py`, `duplicate_detector.py`); keep heuristics localized here.
- `ingestion/` orchestrates validation and processing stages; place shared checks in `validators.py` and long-running work in `processors.py`.
- CLI utilities live in `scripts/` (e.g., `init_db.py`, `import_statements.py`), while `receipt_scanning_tools/` exposes menu-driven helpers such as `manual_entry.py` and `delete_expenses_by_date.py`.
- Tests live in `tests/` with fixtures under `tests/sample_data/`.

## Build, Test, and Development Commands
- Use the isolated environment `/home/adamsl/planner/.venv/`.
- Initialize or reset schema via `python scripts/init_db.py`; replay imports with `python scripts/import_statements.py import-file --org-id 1 tests/sample_data/bank_statement.csv`.
- Launch the CLI via `python receipt_scanning_tools/receipt_tools_menu.py`; Smart Menu automation runs through `python smart_menu/run_smart_menu_system.py`.
- Run the curated suite through `python tests/run_tests.py all`, or use `pytest --maxfail=1 --cov`.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indents, `snake_case` for functions/modules, and `CamelCase` for classes; new parsers must be named `*_parser.py`.
- Format with `black .` before committing, then lint via `flake8`; address warnings instead of suppressing them.
- Keep SQL migrations in dedicated `.sql` files and add docstrings on public interfaces that span modules.
- Always put a space after non-empty parenthesis and brackets and a space before non-empty parenthesis and brackets.

## Testing Guidelines
- Unit and integration tests live in `tests/test_<area>.py`; reuse fixtures from `tests/sample_data/` and create new fixtures there when necessary.
- Coverage is gated at 80% (`pytest.ini`); tag slow or DB-heavy cases with `@pytest.mark.slow` or `@pytest.mark.database`.
- When adding CLI or parser features, add regression cases that parse a real fixture and assert resulting DB rows through repository helpers.

## Commit & Pull Request Guidelines
- Keep commit subjects under ~60 characters and mention the subsystem (`ingestion`, `receipt-tools`, etc.) for quick scans.
- PR descriptions should summarize behavior changes, call out schema or pipeline impacts, link to issues, and attach CLI/test output or menu screenshots.
- Highlight any backward-incompatible parser or DB changes and outline reproduction steps so reviewers can replay imports with `tests/sample_data/`.

## Security & Configuration Tips
- Never commit `.env` or credentials—copy from `.env.example` and load via `app.config.settings`.
- Run schema updates through `scripts/` modules rather than ad-hoc SQL, and scrub sensitive values from sample fixtures before committing.

## Important Menu Guidelines
- When asked to edit the menu system, use the smart menu system that we have available here:
```/home/adamsl/planner/nonprofit_finance_db/receipt_scanning_tools/smart_menu```