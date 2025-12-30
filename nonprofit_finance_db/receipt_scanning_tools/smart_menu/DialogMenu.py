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
            code, tag = d.menu("\nPlease select an option:", choices=menu_items)

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