from remi.gui import *

from UIConstants import uiTextHeight

class FileMenuBuilder:
    @staticmethod
    def build(parent):
        menu = Menu(width='100%', height='30px')
        m1 = MenuItem('File', width=100, height=uiTextHeight)
        
        mNew = MenuItem('New', width=100, height=uiTextHeight)
        mOpen = MenuItem('Open', width=100, height=uiTextHeight)
        mSave = MenuItem('Save', width=100, height=uiTextHeight)
        mSaveAs = MenuItem('Save As', width=100, height=uiTextHeight)
        mReload = MenuItem('Reload', width=100, height=uiTextHeight)
        mExit = MenuItem('Exit', width=100, height=uiTextHeight)
        
        # TODO
        # how to add click handlers:
        # m12.onclick.do(parent.menu_open_clicked)
        # m111.onclick.do(parent.menu_save_clicked)
        # etc.

        menu.append(m1)
        m1.append([mNew, mOpen, mSave, mSaveAs, mReload, mExit])
        menubar = MenuBar(width='100%', height='30px')
        menubar.append(menu)
        return menubar