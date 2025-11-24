
import sys
import traceback
from letta.server.rest_api.app import start_server

print("Starting Letta server via Python script...")
try:
    start_server(host="127.0.0.1", port=8283, debug=True)
except Exception:
    traceback.print_exc()
except SystemExit as e:
    print(f"SystemExit: {e}")
