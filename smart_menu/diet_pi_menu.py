import os, sys
from MenuManager import MenuManager
# from Menu import Menu
from Menu import Menu
# sys.path.append( os.path.expanduser( "~" ) + '/the_function_caller' )
HOME = os.path.expanduser( "~" )
if __name__ == "__main__":
    config_path = f"{ HOME }/rpi-rgb-led-matrix/pickle_cpp/.a_smartmenu/smart_menu/menu_configurations/diet_pi.json"

    menu = Menu()
    menu_manager = MenuManager(menu, config_path )
    menu_manager.load_menus()
    menu.display_and_select(menu_manager)
