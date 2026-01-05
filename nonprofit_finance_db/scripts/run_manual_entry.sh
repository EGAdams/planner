#!/bin/bash
# Wrapper script to run manual_entry.py with virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the main project virtual environment
source /home/adamsl/planner/.venv/bin/activate

# Run the manual entry script
python3 "${SCRIPT_DIR}/receipt_scanning_tools/manual_entry.py" "$@"
