from ConfigReader import ConfigReader
from Menu import Menu
# from DialogMenu import DialogMenu
from MenuItem import MenuItem
from CommandExecutor import CommandExecutor
import json
from SmartMenuItem import SmartMenuItem

# and for the DialogMenu...
import shutil
import os

class MenuManager:
    def __init__(self, menu: Menu, config_path: str):
        self.menu = menu
        self.config_path = config_path

    def load_menus(self):
        """Loads the menu items from the configuration file."""
        config_data = ConfigReader.read_config(self.config_path)
        for item_config in config_data:
            print( item_config.get('working_directory', '' ))
            menu_item = self._create_menu_item(item_config)
            self.menu.add_item(menu_item)

    def _create_menu_item(self, item_config):
        """Creates a menu item from configuration, handling submenus recursively."""
        # Check if this item has a submenu
        if 'submenu' in item_config and item_config['submenu']:
            # Create a submenu
            submenu = Menu()
            for sub_item_config in item_config['submenu']:
                sub_menu_item = self._create_menu_item(sub_item_config)
                submenu.add_item(sub_menu_item)
            # Create a SmartMenuItem with the submenu
            return SmartMenuItem(
                title=item_config['title'],
                sub_menu=submenu
            )
        else:
            # Create a regular MenuItem
            return MenuItem(
                title=item_config['title'],
                action=item_config.get('action', ''),
                working_directory=item_config.get('working_directory', ''),
                open_in_subprocess=item_config.get('open_in_subprocess', False),
                use_expect_library=item_config.get('use_expect_library', False)
            )

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
        print("Adding a new menu item...")
        title = input("Enter the title for the new menu item: ")
        is_submenu = input("Is this a submenu? (yes/no): ").lower() == 'yes'

        if is_submenu:
            new_menu_item = SmartMenuItem(title, sub_menu=Menu())
            print("Submenu added. Remember to add items to this submenu.")
        else:
            action = input("Enter the command to execute: ")
            working_directory = input("Enter the full path to the directory: ")
            open_in_subprocess = input("Should this command open in a separate window (yes/no)? ").lower() == 'yes'
            use_expect_library = input("Should use the Expect library (yes/no)? ").lower() == 'yes'
            new_menu_item = SmartMenuItem(title, action, working_directory, open_in_subprocess, use_expect_library)

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
