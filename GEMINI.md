# GEMINI.md

## Project Overview

This project is a memory-enhanced project management system called "planner". It's built with Retrieval-Augmented Generation (RAG) technology to help freelance AI consultants track projects, clients, and conversations. The system uses a command-line interface (CLI) for interaction and is designed to be integrated with the Claude AI assistant.

The core of the project is a RAG system that uses ChromaDB for vector storage and `sentence-transformers` for text embeddings. The system can ingest various document types, including client profiles, project details, meeting notes, and more. It provides semantic search capabilities and can generate context-aware responses.

The project is well-structured, with separate directories for the RAG system, data models, and utility functions. It also includes a comprehensive suite of tests.

## Building and Running

### Setup

To set up the project and install dependencies, run:

```bash
python setup_and_test.py
```

### Initialize the system

To initialize the RAG system, run:

```bash
python main.py init
```

### Running the CLI

The main entry point for the CLI is `main.py`. You can use it to interact with the RAG system. Here are some examples:

*   **Ingest a document:**
    ```bash
    python main.py ingest /path/to/document.md --doc_type=client_profile
    ```

*   **Search the knowledge base:**
    ```bash
    python main.py search "project status"
    ```

*   **Get a project overview:**
    ```bash
    python main.py project "ProjectName"
    ```

*   **Get a client overview:**
    ```bash
    python main.py client "ClientName"
    ```

### Testing

The project uses `pytest` for testing. To run the tests, you will likely need to run:

```bash
pytest
```

## Development Conventions

*   **Code Style:** The project uses `black` for code formatting and `flake8` for linting.
*   **Typing:** The project uses type hints and `mypy` for static type checking.
*   **CLI:** The CLI is built with `typer`.
*   **Dependencies:** Python dependencies are managed with `pip` and a `requirements.txt` file.
*   **Modularity:** The project is highly modular, with a clear separation of concerns between the RAG system, the CLI, and other components.
