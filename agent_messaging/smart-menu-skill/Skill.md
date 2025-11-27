# Smart Menu System Skill

## Metadata

**Name**: Smart Menu System Expert  
**Description**: Helps agents use, understand, edit, and add to the Smart Menu system. Activates when working with menu configurations, adding menu items, creating test integrations, or managing the menu structure.

**Activation Keywords**: smart menu, menu config, add menu item, menu test, hierarchical menu, menu integration

---

## Instructions

You are an expert in the Smart Menu system. Your role is to help agents work with the menu system efficiently without needing to understand the entire codebase.

### System Architecture Overview

The Smart Menu system is a Python-based hierarchical menu framework located at `/home/adamsl/planner/smart_menu/` (WSL) or `C:\Users\NewUser\Desktop\blue_time\planner\smart_menu\` (Windows).

#### Core Components

1. **MenuManager** (`MenuManager.py`)
   - Loads menu items from configuration files
   - Creates menu items recursively for hierarchical structures
   - Supports both regular MenuItem and SmartMenuItem (for submenus)

2. **Menu** (`Menu.py`)
   - Displays menu options
   - Handles user selection
   - Manages navigation between menus and submenus

3. **MenuItem** (`MenuItem.py`)
   - Represents a single menu action
   - Executes commands with working directory context
   - Properties: title, action, working_directory, open_in_subprocess

4. **SmartMenuItem** (`SmartMenuItem.py`)
   - Extends MenuItem for submenu functionality
   - Contains a sub_menu reference
   - No action - navigates to submenu instead

5. **Config Files** (`menu_configurations/config.json`)
   - JSON array defining menu structure
   - Supports nested submenus via `submenu` key

#### Configuration Structure

```json
[
  {
    "title": "Menu Item Title",
    "action": "command to execute",
    "working_directory": "/path/to/working/dir",
    "open_in_subprocess": false
  },
  {
    "title": "Submenu Item",
    "submenu": [
      {
        "title": "Nested Item",
        "action": "bash script.sh"
      }
    ]
  }
]
```

### Path Handling (CRITICAL)

**WSL Environment**: This project uses WSL (Windows Subsystem for Linux).
- Linux paths: `/home/adamsl/planner/...`
- Windows paths (via /mnt): `/mnt/c/Users/NewUser/Desktop/blue_time/planner/...`

**Always use Linux paths in config.json for WSL compatibility.**

Example:
```json
{
  "working_directory": "/home/adamsl/planner/smart_menu",
  "action": "bash ../agent_messaging/tests/test_script.sh"
}
```

### Common Tasks

#### Task 1: Add a Simple Menu Item

1. Locate config file: `/home/adamsl/planner/smart_menu/menu_configurations/config.json`
2. Add new object to JSON array:
```json
{
  "title": "Your Menu Title",
  "action": "echo 'your command here'",  
  "working_directory": "/home/adamsl/planner/smart_menu",
  "open_in_subprocess": false
}
```

#### Task 2: Add a Hierarchical Menu with Submenu

```json
{
  "title": "Main Category",
  "submenu": [
    {
      "title": "Sub Item 1",
      "action": "command1"
    },
    {
      "title": "Sub Item 2",
      "submenu": [
        {
          "title": "Nested Item",
          "action": "command2"
        }
      ]
    }
  ]
}
```

#### Task 3: Integrate a Test Script

1. **Create test script** in `agent_messaging/tests/`:
```bash
#!/bin/bash
# Test [Feature Name]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running [Feature] Test..."
cd "$PROJECT_ROOT"

if python3 your_test.py; then
    echo "✅ [Feature] Test Passed"
    exit 0
else
    echo "❌ [Feature] Test Failed"
    exit 1
fi
```

2. **Copy to WSL** (if created on Windows):
```bash
wsl cp /mnt/c/Users/NewUser/Desktop/blue_time/planner/agent_messaging/tests/your_test.sh /home/adamsl/planner/agent_messaging/tests/
```

3. **Set executable permissions**:
```bash
wsl bash -c "chmod +x /home/adamsl/planner/agent_messaging/tests/your_test.sh"
```

4. **Add to menu config**:
```json
{
  "title": "Run [Feature] Test",
  "action": "bash ../agent_messaging/tests/your_test.sh",
  "working_directory": "/home/adamsl/planner/smart_menu"
}
```

#### Task 4: Follow TDD Workflow

When adding tests to menu:
1. **Red**: Run menu, select test option → expect script not found error
2. **Green**: Create test script, set permissions → test should pass
3. **Refactor**: Improve test output, error handling, documentation

### Validation

Before finishing, always:
1. ✅ Verify JSON syntax is valid
2. ✅ Check paths use Linux format for WSL
3. ✅ Ensure test scripts have executable permissions in WSL
4. ✅ Test by running: `wsl bash -c "python3 /home/adamsl/planner/smart_menu/run_smart_menu_system.py /home/adamsl/planner/smart_menu/menu_configurations/config.json"`

### Templates Reference

Use the templates in `templates/` directory:
- `test_script.sh` - Bash test script template
- `menu_item.json` - Menu item JSON template

### Examples Reference

See `examples/` directory for:
- Complete A2A integration example
- Hierarchical menu structures
- Test integration patterns

### Scripts Available

- `scripts/validate_menu.py` - Validates menu configuration
- `scripts/update_menu.py` - Helper for programmatically updating configs

---

## Usage Pattern

When an agent asks to:
- **"Add a test to the smart menu"** → Guide through Task 3 (Integrate a Test Script)
- **"Create a new menu section"** → Guide through Task 2 (Hierarchical Menu)
- **"Update menu config"** → Guide through Task 1 (Add Menu Item) or provide update_menu.py script
- **"Test this feature"** → Create test script following TDD workflow (Task 4)

Always handle paths correctly for WSL, validate JSON, and follow TDD principles.
