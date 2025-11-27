#!/bin/bash
# RAG Memory System - Shell Functions for Quick Access
# Usage: source rag_aliases.sh

# Get the directory where this script is located
RAG_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Quick memory commands (using functions for better compatibility)
mem-remember() { python3 "$RAG_DIR/main.py" note "$@"; }
mem-search() { python3 "$RAG_DIR/main.py" search "$@"; }
mem-recent() { python3 "$RAG_DIR/main.py" recent "$@"; }
mem-status() { python3 "$RAG_DIR/main.py" status "$@"; }
mem-project() { python3 "$RAG_DIR/main.py" project "$@"; }
mem-client() { python3 "$RAG_DIR/main.py" client "$@"; }

# Artifact logging
mem-error() { python3 "$RAG_DIR/main.py" artifact "$@"; }
mem-gotcha() { python3 "$RAG_DIR/main.py" gotcha "$@"; }
mem-perf() { python3 "$RAG_DIR/main.py" perf "$@"; }
mem-deploy() { python3 "$RAG_DIR/main.py" deploy "$@"; }
mem-dependency() { python3 "$RAG_DIR/main.py" dependency "$@"; }

# Search artifacts
mem-find() { python3 "$RAG_DIR/main.py" search-artifacts "$@"; }

# Context retrieval
mem-context() { python3 "$RAG_DIR/main.py" context "$@"; }

# Show available types
mem-types() { python3 "$RAG_DIR/main.py" types; }

# Help
mem-help() { python3 "$RAG_DIR/main.py" --help; }

# Export functions so they work in subshells
export -f mem-remember mem-search mem-recent mem-status mem-project mem-client
export -f mem-error mem-gotcha mem-perf mem-deploy mem-dependency mem-find
export -f mem-context mem-types mem-help

echo "✅ RAG Memory functions loaded!"
echo "Try: mem-status, mem-search \"query\", mem-recent --limit 5"
echo "Or import in Python: from rag_tools import remember, recall"
