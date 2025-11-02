# GEMINI.md

## Project Overview

This project is a Python-based system for parsing and integrating bank statements for nonprofit organizations. It provides a command-line interface (CLI) for importing bank statements, detecting duplicates, validating data, and automatically categorizing transactions.

The project is well-structured, with separate modules for parsing, duplicate detection, data ingestion, and database interaction. It uses a MySQL database to store financial data and provides a comprehensive suite of tests.

## Building and Running

### Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure environment variables:**
    Create a `.env` file in the project root and populate it with your database credentials. You can use `.env.example` as a template.

3.  **Initialize the database:**
    ```bash
    python scripts/init_db.py
    ```

### Running the CLI

The main entry point for the CLI is `scripts/import_statements.py`. You can use it to interact with the system. Here are some examples:

*   **Import a single file:**
    ```bash
    python scripts/import_statements.py import-file --org-id 1 path/to/statement.csv
    ```

*   **Import all files from a directory:**
    ```bash
    python scripts/import_statements.py import-directory --org-id 1 --pattern "*.csv" path/to/statements/
    ```

*   **View import history:**
    ```bash
    python scripts/import_statements.py history --org-id 1
    ```

### Testing

The project uses `pytest` for testing. To run the tests, use the following command:

```bash
python tests/run_tests.py all
```

## Development Conventions

*   **Code Style:** The project uses `black` for code formatting and `flake8` for linting.
*   **Typing:** The project uses type hints and `mypy` for static type checking.
*   **CLI:** The CLI is built with `click` and `rich`.
*   **Dependencies:** Python dependencies are managed with `pip` and a `requirements.txt` file.
*   **Modularity:** The project is highly modular, with a clear separation of concerns between the different components.
