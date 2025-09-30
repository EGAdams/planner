# Repository Guidelines

## Project Structure & Module Organization
- `app/` contains the core domain logic, including `models/`, `repositories/`, and database wiring in `app/db/`.
- `parsers/` provides file-format adapters; implement `BaseParser` when adding CSV, PDF, or OFX readers.
- `detection/` holds duplicate-matching heuristics; tune weights in `matching_algorithms.py` and orchestration in `duplicate_detector.py`.
- `ingestion/` orchestrates validation and processing stages for imports.
- `scripts/` exposes CLI utilities such as `import_statements.py` and `init_db.py`; `tests/` houses fixtures under `sample_data/`.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate` prepares an isolated Python 3.8+ environment.
- `pip install -r requirements.txt` installs runtime, linting, and testing dependencies.
- `python scripts/init_db.py` provisions the schema defined in `transaction_schema.sql`.
- `python scripts/import_statements.py import-file --org-id 1 path/to/file.csv` exercises the full ingest pipeline on a sample file.
- `python tests/run_tests.py all` executes the curated suite (parsers, detection, ingestion); `pytest` mirrors it with coverage reporting.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation; modules and functions use `snake_case`, while classes use `CamelCase`.
- Format code via `black .` before committing, and avoid manual tweaks to its output.
- Lint with `flake8` to catch unused imports, complexity spikes, and style drift.
- Name new parsers `*_parser.py` and place shared validation helpers in `ingestion/validators.py`.

## Testing Guidelines
- Add targeted cases in `tests/test_<area>.py` and reuse fixtures from `tests/sample_data/`.
- Coverage gates are enforced at 80% (`pytest.ini`); failing thresholds will block merges.
- Mark slow or DB-dependent checks with `@pytest.mark.slow` or `@pytest.mark.database` for selective runs.
- Regenerate HTML coverage via `pytest --cov --cov-report=html:htmlcov` when reviewing gaps.

## Commit & Pull Request Guidelines
- Recent history favors concise, descriptive subjects (e.g., `added database setup instructions`); keep them under ~60 characters.
- Reference the subsystem touched and note schema or pipeline impacts in the body of the PR.
- Link related issues, include reproduction steps or CLI output, and attach logs when behavior changes.

## Security & Configuration Tips
- Never commit `.env` or credentials; populate a local copy from `.env.example`.
- Run schema updates through `scripts/` so reviewers can replay database changes.
- Scrub sensitive values from sample files before placing them under `tests/sample_data/`.
