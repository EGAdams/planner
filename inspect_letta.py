import letta_client
print(dir(letta_client))
print(f"File: {letta_client.__file__}")
try:
    from letta_client import Letta
    print("Letta imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")

try:
    from letta_client import Client
    print("Client imported successfully")
except ImportError:
    pass
