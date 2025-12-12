# Persona
World-class Python Developer specialized with usning the Gang of Four design patterns.

# Your task
- In the source code below I want to be able to add MenuItem objects to the menu that not only builds executable actions but also can add another smart menu like the one depicted in the system below.
- Don't worry about explaining the code, just focus on the task at hand.
- You don't have to rewrite all of the source code below, just add another object that will perform the new features and show me what other modifications that we would need to do to the original source code to make it work.

# Source code to use as a guide.
```python
import subprocess
import os
from MenuItem import MenuItem  # Assuming MenuItem is defined in MenuItem.py

class CommandExecutor:
    @staticmethod
    def execute_command(menu_item):
        """Executes the command associated with a given MenuItem."""
        if not isinstance(menu_item, MenuItem):
            raise ValueError("menu_item must be an instance of MenuItem")

        original_dir = os.getcwd()  # Save the original directory
        try:
            # Change the working directory if specified
            if menu_item.working_directory:
                os.chdir(menu_item.working_directory)
            
            # Execute command in a subprocess or current process
            if menu_item.open_in_subprocess:
                subprocess.run(menu_item.action, shell=True, check=True)
            else:
                # This is a placeholder for executing the command without opening a new subprocess.
                # In reality, this might involve more direct execution methods depending on the command.
                os.system(menu_item.action)
        except Exception as e:
            print(f"Error executing command {menu_item.action}: {e}")
        finally:
            os.chdir(original_dir)  # Restore the original directory

import json

class ConfigReader:
    @staticmethod
    def read_config(file_path):
        """
        Reads a configuration file and returns its contents as a data structure.
        
        This method attempts to open and read a JSON configuration file specified by `file_path`. 
        If successful, it returns the contents of the file as a Python data structure (typically a dictionary or a list, 
        depending on the JSON structure). If the file cannot be found, or if the file is not valid JSON, appropriate 
        error messages are printed, and an empty list is returned.
        
        Parameters:
        - file_path (str): The path to the configuration file that is to be read.
        
        Returns:
        - list/dict: The content of the configuration file parsed from JSON. If an error occurs, an empty list is returned.
        
        Exceptions:
        - FileNotFoundError: If the file specified by `file_path` does not exist, a message is printed indicating that 
          the file was not found, and an empty list is returned.
        - json.JSONDecodeError: If the file specified by `file_path` is not valid JSON, a message is printed indicating 
          that there was an error decoding the file, and an empty list is returned.
        """
        try:
            with open(file_path, 'r') as config_file:
                config_data = json.load(config_file)
                return config_data
        except FileNotFoundError:
            print(f"The configuration file {file_path} was not found.")
            return []
        except json.JSONDecodeError:
            print("Error decoding the configuration file. Please ensure it is valid JSON.")
            return []


# import MenuItem
from MenuItem import MenuItem
# code to import pythondialog
import dialog




class DialogMenu:
    def __init__(self, items=None):
        self.items = items if items else []

    def add_item(self, item):
        self.items.append(item)


    def display_and_select(self, menu_manager):
        d = dialog.Dialog(dialog="dialog")

        # Prepare the menu items along with an "Exit" and "Add menu item" option
        menu_items = [(str(index + 1), item.title) for index, item in enumerate(self.items)]
        menu_items.append(("Exit", "Exit this menu"))
        menu_items.append(("Add", "Add a menu item"))

        while True:
            code, tag = d.menu("Please select an option:", choices=menu_items)

            if code == d.OK:
                if tag == "Exit":
                    break
                elif tag == "Add":
                    menu_manager.add_menu_item()
                else:
                    # Convert tag back to index and execute the selected item
                    index = int(tag) - 1
                    if index < len(self.items):
                        self.items[index].execute()
            else:
                # This handles the case where the user presses 'Cancel' or closes the dialog
                print( "Operation cancelled or closed. Exiting..." )
                break

    
    

    def add_new_item(self):
        title = input("Enter title for new item: ")
        command = input("Enter command to execute: ")
        working_directory = input("Enter the working directory (optional): ")
        open_in_subprocess = input("Open in a subprocess? (yes/no): ").lower() == 'yes'
        use_expect_library = input("Use the expect library? (yes/no): ").lower() == 'yes'
        new_item = MenuItem( title, command, working_directory, open_in_subprocess, use_expect_library )
        self.add_item( new_item )
    
    def to_dict_list(self):
        """Serializes the menu's items into a list of dictionaries."""
        return [item.to_dict() for item in self.items]

def main():
    menu = Menu()
    # Example adding initial menu items
    menu.add_item(MenuItem("List current directory", "ls"))
    menu.display_and_select()

if __name__ == "__main__":
    main()
# import MenuItem
from MenuItem import MenuItem

class Menu:
    def __init__(self, items=None):
        self.items = items if items else []

    def add_item(self, item):
        self.items.append(item)

    def display_and_select(self, menu_manager):
        while True:
            for index, item in enumerate(self.items, start=1):
                print(f"{index}. {item.title}")
            print(f"{len(self.items) + 1}. Exit this menu")
            print(f"{len(self.items) + 2}. Add a menu item")

            choice = input("Please select an option: ")
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(self.items):   #
                    self.items[choice - 1].execute() # Shabaaam! This is the line that executes the command
                elif choice == len(self.items) + 1:  #
                    break
                elif choice == len(self.items) + 2:
                    menu_manager.add_menu_item()
            else:
                print("Invalid selection. Please try again.")
    
    

    def add_new_item(self):
        title = input("Enter title for new item: ")
        command = input("Enter command to execute: ")
        working_directory = input("Enter the working directory (optional): ")
        open_in_subprocess = input("Open in a subprocess? (yes/no): ").lower() == 'yes'
        use_expect_library = input("Use the expect library? (yes/no): ").lower() == 'yes'
        new_item = MenuItem( title, command, working_directory, open_in_subprocess, use_expect_library )
        self.add_item( new_item )
    
    def to_dict_list(self):
        """Serializes the menu's items into a list of dictionaries."""
        return [item.to_dict() for item in self.items]

def main():
    menu = Menu()
    # Example adding initial menu items
    menu.add_item(MenuItem("List current directory", "ls"))
    menu.display_and_select()

if __name__ == "__main__":
    main()
import os
import subprocess
class MenuItem:
    def __init__(self, title, action, working_directory, open_in_subprocess, use_expect_library):
        self.title = title
        self.action = action
        self.working_directory = working_directory
        self.open_in_subprocess = open_in_subprocess
        self.use_expect_library = use_expect_library

    def execute(self):
        try:
            final_command = self.action
            # Change directory if specified and necessary
            if self.working_directory:
                os.chdir(self.working_directory)
            
            if self.open_in_subprocess:
                # Open the command in a new subprocess
                process = subprocess.Popen(final_command, shell=True)
                process.communicate()  # Wait for the command to complete if needed
            else:
                # Execute the command in the current process
                subprocess.run(final_command, shell=True, check=True)
            
            print(f"Command executed: {self.action}")
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
        finally:
            # If we changed directories, change back to the original
            if self.working_directory:
                os.chdir(os.path.dirname(__file__))
        
    def to_dict(self):
        """Serializes the MenuItem into a dictionary."""
        return {
            "title": self.title,
            "action": self.action,
            "working_directory": self.working_directory,
            "open_in_subprocess": self.open_in_subprocess,
            "open_in_subprocess": self.use_expect_library
        }
from ConfigReader import ConfigReader
from Menu import Menu
# from DialogMenu import DialogMenu
from MenuItem import MenuItem
from CommandExecutor import CommandExecutor
import json

# and for the DialogMenu...
import shutil
import os

class MenuManager:
    def __init__(self, menu, config_path):
        self.menu = menu
        self.config_path = config_path

    def load_menus(self):
        """Loads the menu items from the configuration file."""
        config_data = ConfigReader.read_config(self.config_path)
        for item_config in config_data:
            menu_item = MenuItem(
                title=item_config['title'],
                action=item_config['action'],
                working_directory=item_config.get('workingDirectory', ''),
                open_in_subprocess=item_config.get('openInSubprocess', False),
                use_expect_library=item_config.get('useExpectLibrary', False)
            )
            self.menu.add_item(menu_item)

    def display_menu(self):
        """Displays the menu and handles user input."""
        while True:
            # self.menu.display_and_select()
            choice = input("\nPlease select an option: ")
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(self.menu.items):
                    self.menu.items[choice - 1].execute()
                elif choice == len(self.menu.items) + 1:
                    break  # Exit the menu
                elif choice == len(self.menu.items) + 2:
                    self.add_menu_item()
            else:
                print("Invalid selection. Please try again.")

    def add_menu_item(self):
        """Collects information from the user to add a new menu item."""
        print("Adding a new menu item...")
        title = input("Enter the title for the new menu item: ")
        action = input("Enter the command to execute: ")
        working_directory = input("Enter the full path to the directory: ")
        open_in_subprocess_str = input("Should this command open in a separate window (yes/no)? ")
        use_expect_library_str = input("Should use the Expect library (yes/no)? ")

        open_in_subprocess = open_in_subprocess_str.lower() == 'yes'
        use_expect_library = use_expect_library_str.lower() == 'yes'

        new_menu_item = MenuItem(title, action, working_directory, open_in_subprocess, use_expect_library)
        self.menu.add_item(new_menu_item)
        print("New menu item added successfully.")
        self.save_menus_to_config()

    def save_menus_to_config(self):
        """Serializes and saves the menu structure to the configuration file."""
        config_data = [item.to_dict() for item in self.menu.items]
        with open(self.config_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=4)
        print("Menu configuration saved.")

    def save_to_config(self):
        """Saves the current menu configuration to a file."""
        with open(self.config_path, 'w') as config_file:
            json.dump(self.menu.to_dict_list(), config_file, indent=4)
        print("Menu configuration saved.")
        
    # def add_new_item(self):
    #     # Existing code to add a new item
    #     self.menu.add_item(new_item)
    #     print("New menu item added successfully.")
    #     # Save the updated menu configuration
    #     self.save_to_config()

def main():
    menu = Menu()
    menu_manager = MenuManager(menu, "path_to_config.json")
    menu_manager.load_menus()
    menu.display_and_select(menu_manager)

if __name__ == "__main__":
    main()


from MenuManager import MenuManager
# from Menu import Menu
from Menu import Menu
if __name__ == "__main__":
    config_path = "/home/adamsl/linuxBash/python_menus/smart_menu/config.json"

    menu = Menu()
    menu_manager = MenuManager(menu, config_path )
    menu_manager.load_menus()
    menu.display_and_select(menu_manager)
```
