# start_services.ps1
# This script starts the required services for the A2A collective:
# 1. Letta server (memory backend)
# 2. WebSocket server (optional, for real-time transport)

# Ensure you have Letta installed: pip install letta
# Start Letta server (default runs on http://localhost:8283)
Write-Host "Starting Letta server..."
Start-Process -NoNewWindow -FilePath "letta" -ArgumentList "server" -RedirectStandardOutput "letta_server.log" -RedirectStandardError "letta_server_err.log"

# Optional: start a simple WebSocket server if you have one.
# Replace the command below with your actual WebSocket server implementation.
# Example placeholder using websockets library (install via pip install websockets):
# python -m websockets.server --host 0.0.0.0 --port 3030
Write-Host "Starting WebSocket server (placeholder)..."
# Uncomment and adjust the line below to start your real WebSocket server.
# Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m", "websockets.server", "--host", "0.0.0.0", "--port", "3030" -RedirectStandardOutput "ws_server.log" -RedirectStandardError "ws_server_err.log"

Write-Host "All services started. Check the log files for output."
