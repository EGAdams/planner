import sys
from MenuManager import MenuManager
# from Menu import Menu
from Menu import Menu


if __name__ == "__main__":
    if len( sys.argv ) == 2:
        config_path = sys.argv[ 1 ]
    else:
        config_path = "./menu_configurations/config.json"

    menu = Menu()
    menu_manager = MenuManager(menu, config_path )
    menu_manager.load_menus()
    menu.display_and_select(menu_manager)
