export EXECUTOR_WORKSPACE_ROOT="/home/adamsl/planner/nonprofit_finance_db/receipt_scanning_tools"
export EXECUTOR_ALLOW_CMDS="python,python3,pytest,git,node,npm"

pkill -f "uvicorn.*8787" || true
export EXECUTOR_TOKEN="6c9f1e4b5a2d8f7c0b3e9a4d7f2c1e8"
uvicorn executor_server:app --app-dir "/home/adamsl/planner/nonprofit_finance_db/receipt_scanning_tools/server_tools" --host 0.0.0.0 --port 8787 --reload



# curl -sS -X POST http://localhost:8787/run \
#   -H "Authorization: Bearer 6c9f1e4b5a2d8f7c0b3e9a4d7f2c1e8" \
#   -H "Content-Type: application/json" \
#   -d '{"command":"pwd","cwd":"."}'

# hostname -I | awk '{print $1}'
# 172.26.163.131 -- This is the windows eleven dell on January 5, 2026


# netsh interface portproxy add v4tov4 `
#   listenaddress=0.0.0.0 listenport=8787 `
#   connectaddress=172.26.163.131 connectport=8787

# uvicorn executor_server:app --host 0.0.0.0 --port 8787 --reload
