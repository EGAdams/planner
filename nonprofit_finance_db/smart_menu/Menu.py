# import MenuItem
import os
from MenuItem import MenuItem

class Menu:
    def __init__(self, items=None):
        self.items = items if items else []

    def add_item(self, item):
        self.items.append(item)

    def display_and_select(self, menu_manager=None):
        os.system('clear;echo;echo;echo;echo;echo')  # Clear the console for better readability
        os.system( 'echo       "  ==================" ' )
        os.system( 'echo "  === Smart Menu ===";' )
        os.system( 'echo "  =================="; echo;' )

        while True:
            for index, item in enumerate(self.items, start=1):
                print(f"  {index}. {item.title}")
            print(f"  {len(self.items) + 1}. Exit this menu")
            # print(f"{len(self.items) + 2}. Add a menu item")

            choice = input("\n  Please select an option: ")
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(self.items):   #
                    self.items[choice - 1].execute() # Shabaaam! This is the line that executes the command
                elif choice == len(self.items) + 1:  #
                    break
                elif choice == len(self.items) + 2:
                    if menu_manager:
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
    menu.add_item(MenuItem("List current directory", "ls", "", False, False))
    menu.display_and_select()

if __name__ == "__main__":
    main()