#!/bin/bash
# Start the Daily Expense Categorizer API server

cd /home/adamsl/planner/nonprofit_finance_db

# Activate virtual environment
source venv/bin/activate

# Start the server
python3 api_server.py
