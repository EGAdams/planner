import json
import os

# Define paths
current_dir = os.getcwd()
config_path = os.path.abspath(os.path.join(current_dir, "..", "smart_menu", "menu_configurations", "config.json"))

print(f"Updating config at: {config_path}")

# New menu structure
new_menu_item = {
    "title": "A2A Agent Collective",
    "submenu": [
        {
            "title": "Phase 1: Infrastructure",
            "submenu": [
                {
                    "title": "A2A collective Hub",
                    "submenu": [
                        {
                            "title": "Run Agent Discovery Test",
                            "action": "bash ../agent_messaging/tests/test_agent_discovery.sh",
                            "working_directory": "/home/adamsl/planner/smart_menu"
                        },
                        {
                            "title": "Run Delegation Test", 
                            "action": "bash ../agent_messaging/tests/test_delegation.sh",
                            "working_directory": "/home/adamsl/planner/smart_menu"
                        }
                    ]
                },
                {
                    "title": "Agent discovery system",
                    "action": "echo 'Tests coming soon...'"
                },
                {
                    "title": "Unified memory with Fallback",
                    "submenu": [
                        {
                            "title": "Run Memory System Test",
                            "action": "bash ../agent_messaging/tests/test_memory_system.sh",
                            "working_directory": "/home/adamsl/planner/smart_menu"
                        }
                    ]
                },
                {
                    "title": "Transport factory with fallback",
                    "action": "echo 'Tests coming soon...'"
                },
                {
                    "title": "Voice capability scaffolding",
                    "action": "echo 'Tests coming soon...'"
                },
                {
                    "title": "Service management scripts",
                    "action": "echo 'Tests coming soon...'"
                }
            ]
        }
    ]
}

try:
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    # Replace the first item (A2A Agent Collective)
    # We assume it's the first item based on previous inspection
    if config_data[0]['title'] == "A2A Agent Collective" or config_data[0]['title'] == "A2A Communicating Agents":
        print("Found target menu item. Replacing...")
        config_data[0] = new_menu_item
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        print("Config updated successfully.")
    else:
        print("Could not find 'A2A Agent Collective' or 'A2A Communicating Agents' at index 0.")
        # Fallback search
        for i, item in enumerate(config_data):
            if item.get('title') == "A2A Agent Collective" or item.get('title') == "A2A Communicating Agents":
                print(f"Found target at index {i}. Replacing...")
                config_data[i] = new_menu_item
                with open(config_path, 'w') as f:
                    json.dump(config_data, f, indent=4)
                print("Config updated successfully.")
                break

except Exception as e:
    print(f"Error updating config: {e}")
