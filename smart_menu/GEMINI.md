# Smart Menu System

## Project Overview
The **Smart Menu System** is a Python-based Command Line Interface (CLI) application designed to orchestrate and streamline various local development and administrative tasks. It functions as a central hub for managing complex workflows, specifically tailored for:

*   **Letta / A2A Communicating Agents:** Managing the lifecycle (start, stop, restart, diagnostic) of orchestrator, coder, and tester agents.
*   **Finance & Receipt Tools:** Running Python scripts for receipt processing, data entry, and Google Sheets integration.
*   **System Management:** General utility commands and workspace management.

## Key Components

*   **Entry Points:**
    *   `run_smart_menu_system.py`: The primary script to launch the menu interface.
    *   `smart_menu_system.py`: Alternative entry point containing the main execution logic.
*   **Core Logic:**
    *   `MenuManager.py`: Manages the loading of configurations, creation of menu items, and saving of changes. Handles the "smart" aspects like submenu recursion.
    *   `Menu.py`: Handles the display of menu options and user input loops.
    *   `MenuItem.py` & `SmartMenuItem.py`: Define the structure of individual menu entries. `SmartMenuItem` extends functionality to support submenus and specific execution contexts (e.g., subprocesses).
    *   `ConfigReader.py`: Utilities for reading and parsing the JSON configuration.
    *   `CommandExecutor.py`: (Inferred) Handles the actual execution of shell commands defined in the menu items.
*   **Configuration:**
    *   `menu_configurations/`: Directory storing JSON configuration files.
    *   `menu_configurations/config.json`: The active, default configuration file defining the current menu structure and tasks.

## Usage

### Running the Menu
To start the interactive menu system, run the following command from the project root:

```bash
python3 run_smart_menu_system.py
```

### Loading a Specific Configuration
You can pass a specific configuration file as an argument:

```bash
python3 run_smart_menu_system.py ./menu_configurations/diet_pi.json
```

If no argument is provided, it defaults to `./menu_configurations/config.json`.

## Configuration Structure (`config.json`)
The menu is driven by a JSON array of objects. Each object represents a menu item or a submenu.

**Properties:**
*   `title` (string): The text displayed in the menu.
*   `action` (string, optional): The shell command to execute. Required if `submenu` is not present.
*   `working_directory` (string, optional): The directory where the command should be executed.
*   `submenu` (array, optional): A nested list of menu item objects. If present, this item becomes a folder/submenu.
*   `open_in_subprocess` (boolean, optional): If `true`, the command runs in a separate process/window (implementation dependent).
*   `use_expect_library` (boolean, optional): Configures execution for interactive commands requiring `expect`-like behavior.

**Example:**
```json
{
    "title": "Start Service",
    "action": "./start_service.sh",
    "working_directory": "/path/to/service",
    "open_in_subprocess": true
}
```

## Development Conventions
*   **Python:** The project uses standard Python 3 conventions.
*   **Pathing:** Configuration paths are often absolute or relative to the `planner` root.
*   **Modularity:** New functionality should ideally be added as standalone scripts referenced in the JSON config, rather than hardcoding logic into the menu system itself.
