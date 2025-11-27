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