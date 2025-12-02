# Example: Adding a Menu Item with Test

This example shows how the A2A Agent Collective tests were integrated into the Smart Menu system.

## Goal
Add "Run Agent Discovery Test" to the menu system under:
A2A Agent Collective → Phase 1: Infrastructure → A2A collective Hub

## Steps

### 1. Create the Test Script

File: `agent_messaging/tests/test_agent_discovery.sh`

```bash
#!/bin/bash
# Test Agent Discovery

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running Agent Discovery Test..."
cd "$PROJECT_ROOT"

if python3 run_collective.py; then
    echo "✅ Agent Discovery Test Passed"
    exit 0
else
    echo "❌ Agent Discovery Test Failed"
    exit 1
fi
```

### 2. If we are in a Windows environment, copy to WSL and Set Permissions

```bash
wsl cp /mnt/c/Users/NewUser/Desktop/blue_time/planner/agent_messaging/tests/test_agent_discovery.sh /home/adamsl/planner/agent_messaging/tests/
wsl bash -c "chmod +x /home/adamsl/planner/agent_messaging/tests/test_agent_discovery.sh"
```

### 3. Add to Menu Config

Update `smart_menu/menu_configurations/config.json`:

```json
{
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
            }
          ]
        }
      ]
    }
  ]
}
```

### 4. Test via Menu

#### Powershell
```bash
wsl bash -c "python3 /home/adamsl/planner/smart_menu/run_smart_menu_system.py /home/adamsl/planner/smart_menu/menu_configurations/config.json"
```

#### wsl
```bash
python3 /home/adamsl/planner/smart_menu/run_smart_menu_system.py /home/adamsl/planner/smart_menu/menu_configurations/config.json
```

Navigate: 5 → 1 → 1 → 1

### Result

```
🧪 Running Agent Discovery Test...
📂 Project Root: /home/adamsl/planner/agent_messaging
Discovered 2 agents
- letta (v1.0.0)
- orchestrator (v1.0.0)
✅ Agent Discovery Test Passed
```

## TDD Workflow

1. **Red**: Ran menu before script existed → "script not found" error
2. **Green**: Created script with permissions → test passed
3. **Refactor**: Added clear output formatting with emojis
