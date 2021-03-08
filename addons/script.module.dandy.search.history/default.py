# -*- coding: utf-8 -*-
# Writer (c) 2019, dandy
# Rev. 1.0.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

import resources.lib.SearchHistory as history

ID = 'script.module.dandy.search.history'
ADDON = xbmcaddon.Addon(ID)

def main():
    if (xbmcgui.Dialog().yesno("", "Clean search history?") == True):
        history.clean()

if __name__ == '__main__':
    main()
