#!/usr/bin/env python3
"""
Create or reuse a Gemini File Search store, upload files, wait for indexing,
and (optionally) run a test query.

Requirements:
  pip install google-genai

Auth:
  export GOOGLE_API_KEY=...   # or GEMINI_API_KEY
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Iterable, List, Optional

from google import genai
from google.genai import types


def iter_files(paths: List[str]) -> Iterable[Path]:
    for p in paths:
        path = Path(p).expanduser().resolve()
        if path.is_file():
            yield path
        elif path.is_dir():
            for f in path.rglob("*"):
                if f.is_file():
                    yield f
        else:
            for f in Path().glob(p):
                if f.is_file():
                    yield f


def wait_operation(client: genai.Client, operation, poll_seconds: float = 3.0):
    while not getattr(operation, "done", False):
        time.sleep(poll_seconds)
        operation = client.operations.get(operation)
    return operation


def find_store_by_display_name(client: genai.Client, display_name: str):
    for store in client.file_search_stores.list():
        if getattr(store, "display_name", None) == display_name:
            return store
    return None


def create_or_get_store(client: genai.Client, display_name: str, reuse_if_exists: bool, delete_first: bool):
    existing = find_store_by_display_name(client, display_name)
    if existing and delete_first:
        print(f"Deleting existing store: {existing.name} (force=True)")
        client.file_search_stores.delete(name=existing.name, config={"force": True})
        existing = None

    if existing and reuse_if_exists:
        print(f"Reusing File Search store: {existing.name}")
        return existing

    if existing and not reuse_if_exists:
        print(
            "A store with this display name already exists.\n"
            f"  name: {existing.name}\n"
            "Use --reuse-if-exists or --delete-first to proceed.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Creating File Search store (display_name={display_name!r}) ...")
    store = client.file_search_stores.create(config={"display_name": display_name})
    print(f"Created: {store.name}")
    return store


def upload_file_to_store(client: genai.Client, store_name: str, file_path: Path, chunk_tokens: Optional[int], chunk_overlap: Optional[int]):
    cfg = {"display_name": file_path.name}
    if chunk_tokens or chunk_overlap:
        cfg["chunking_config"] = {
            "white_space_config": {
                "max_tokens_per_chunk": int(chunk_tokens or 200),
                "max_overlap_tokens": int(chunk_overlap or 20),
            }
        }

    print(f"  → Uploading: {file_path}")
    op = client.file_search_stores.upload_to_file_search_store(
        file=str(file_path),
        file_search_store_name=store_name,
        config=cfg,
    )
    wait_operation(client, op)
    print(f"    Indexed: {file_path.name}")


def smoke_test_query(client: genai.Client, store_name: str, query: str, model: str = "gemini-2.5-flash"):
    print("\nRunning smoke test query...")
    resp = client.models.generate_content(
        model=model,
        contents=query,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[store_name]
                    )
                )
            ]
        ),
    )
    print("\n=== Smoke Test Answer ===")
    print(resp.text or "(no text)")
    print("=========================\n")


def main():
    parser = argparse.ArgumentParser(description="Create/prepare a Gemini File Search store and upload files.")
    parser.add_argument("--display-name", required=True, help="Human-friendly display name for the File Search store.")
    parser.add_argument("--paths", nargs="+", help="Files/dirs/globs to upload (e.g., docs/, README.md, '*.pdf').")
    parser.add_argument("--reuse-if-exists", action="store_true", help="Reuse an existing store with the same display name.")
    parser.add_argument("--delete-first", action="store_true", help="Delete any existing store with this display name (force) and recreate.")
    parser.add_argument("--chunk-tokens", type=int, default=None, help="Max tokens per chunk (optional).")
    parser.add_argument("--chunk-overlap", type=int, default=None, help="Overlap tokens between chunks (optional).")
    parser.add_argument("--test-query", default=None, help="Optional question to verify retrieval (e.g., 'Summarize our onboarding policy').")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Model for the smoke test (default: gemini-2.5-flash).")

    args = parser.parse_args()

    client = genai.Client()

    store = create_or_get_store(
        client=client,
        display_name=args.display_name,
        reuse_if_exists=args.reuse_if_exists,
        delete_first=args.delete_first,
    )

    if args.paths:
        files = list(iter_files(args.paths))
        if not files:
            print("No files matched the provided --paths.", file=sys.stderr)
            sys.exit(2)

        print(f"\nUploading {len(files)} file(s) to {store.name} ...")
        for f in files:
            upload_file_to_store(client, store.name, f, args.chunk_tokens, args.chunk_overlap)

    print("\nDone.")
    print(f"File Search store name: {store.name}")
    print("\nSet this env var so your agents can use the store:")
    print(f'  export GEMINI_FILE_SEARCH_STORE="{store.name}"')

    if args.test_query:
        smoke_test_query(client, store.name, args.test_query, model=args.model)


if __name__ == "__main__":
    main()
