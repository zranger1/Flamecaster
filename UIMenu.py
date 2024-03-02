from remi.gui import *

from UIConstants import uiTextHeight


class FileMenuBuilder:
    """
    Unused at the moment, but may need this later.
    """
    @staticmethod
    def build(menuConfig: dict):
        """
        Build the top menu bar for the application

        :param menuConfig: a dictionary of menu item text strings and click handlers
        :return:
        """
        file = MenuItem('File', width="6em", height=uiTextHeight)
        file.style['position'] = 'absolute'
        file.style['left'] = '1em'
        for key in menuConfig:
            m = MenuItem(key, width="8em", height=uiTextHeight)
            m.style['text-align'] = 'left'
            m.style['position'] = 'relative'
            m.style['left'] = '2em'
            m.onclick.do(menuConfig[key])
            file.append(m)

        menu = Menu(width='100%', height=uiTextHeight)
        menu.append(file)
        menubar = MenuBar(width='100%', height=uiTextHeight)
        menubar.append(menu)
        return menubar
