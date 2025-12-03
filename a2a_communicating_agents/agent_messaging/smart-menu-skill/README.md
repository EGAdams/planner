# Smart Menu System - Claude Skill

A Claude Skill that enables agents to work with the Smart Menu system efficiently without needing deep codebase knowledge.

## Purpose

This skill helps agents:
- **Understand** the Smart Menu architecture
- **Add** new menu items and submenus
- **Create** and integrate test scripts
- **Validate** menu configurations
- **Handle** WSL/Windows path differences automatically

## Structure

```
smart-menu-skill/
├── Skill.md              # Main skill instructions
├── README.md             # This file
├── examples/             # Real-world examples
│   ├── add_menu_item.md
│   └── hierarchical_menu.json
├── templates/            # Reusable templates
│   ├── test_script.sh
│   └── menu_item.json
└── scripts/              # Helper scripts
    ├── validate_menu.py
    └── update_menu.py
```

## Installation

### For Claude.ai (Web Interface)

1. **Zip the skill folder**:
```bash
cd agent_messaging
zip -r smart-menu-skill.zip smart-menu-skill/
```

2. **Upload to Claude**:
   - Go to Settings > Capabilities
   - Enable "Skills"
   - Click "Upload skill"
   - Select `smart-menu-skill.zip`

### For Claude API

Prepare the skill package and upload via the API:
```python
# Coming soon - API integration example
```

## Usage

The skill automatically activates when you mention keywords like:
- "smart menu"
- "add menu item"
- "menu test"
- "update menu config"

### Example Prompts

**Add a simple menu item:**
```
Add a menu item to run the dashboard tests
```

**Create hierarchical menu:**
```
Create a submenu for Phase 2 features under A2A Agent Collective
```

**Integrate a test:**
```
Add the test_transport_factory.py to the smart menu under Phase 1
```

## Components Reference

### Main Instruction File
- **Skill.md**: Comprehensive guide on menu system architecture, common tasks, and best practices

### Templates
- **test_script.sh**: Bash script template for test integration
- **menu_item.json**: JSON template for menu items

### Examples
- **add_menu_item.md**: Step-by-step guide from A2A integration
- **hierarchical_menu.json**: Complete multi-level menu structure

### Scripts
- **validate_menu.py**: Validates JSON syntax, structure, and paths
- **update_menu.py**: Programmatically add/remove menu items

## Testing the Skill

After uploading, test with:
```
I need to add a test for the memory system to the smart menu
```

Check Claude's reasoning panel to confirm the skill was loaded and activated.

## Key Features

✨ **Automatic Path Handling**: Knows to use Linux paths for WSL  
✨ **TDD Workflow Integration**: Guides through Red-Green-Refactor  
✨ **Validation**: Built-in config validation  
✨ **Templates**: Ready-to-use templates for common tasks  
✨ **Examples**: Real examples from successful integrations  

## Requirements

- Python 3.x
- WSL (Windows Subsystem for Linux)
- Smart Menu system installed at `/home/adamsl/planner/smart_menu/`

## Future Enhancements

- [ ] API integration examples
- [ ] Automated testing for skill functionality
- [ ] Additional templates for different menu patterns
- [ ] Visual menu structure generator

## Related Skills

After this skill is working, create:
- A2A Agent Communication Skill
- Test Framework Skill
- Dashboard Integration Skill
