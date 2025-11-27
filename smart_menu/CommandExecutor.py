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
