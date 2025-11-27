#
from MenuItem import MenuItem

#/** class SmartMenuItem */
class SmartMenuItem( MenuItem ):
    def __init__(self, title, action=None, working_directory='', open_in_subprocess=False, use_expect_library=False, sub_menu=None):
        super().__init__(title, action, working_directory, open_in_subprocess, use_expect_library)
        self.sub_menu = sub_menu  # This can be another Menu object or None

    def execute(self):
        if self.sub_menu:
            self.sub_menu.display_and_select()
        else:
            super().execute()

    def to_dict(self):
        item_dict = super().to_dict()
        # Serialize submenu if it exists
        if self.sub_menu:
            item_dict['submenu'] = [item.to_dict() for item in self.sub_menu.items]
        return item_dict
