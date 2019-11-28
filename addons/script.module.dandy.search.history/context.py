# -*- coding: utf-8 -*-
# Writer (c) 2019, dandy
# Rev. 1.0.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcgui

import resources.lib.SearchHistory as history

def get_title():
    return xbmc.getInfoLabel("ListItem.Title") if xbmc.getInfoLabel("ListItem.Title") else xbmc.getInfoLabel("ListItem.Label")

def main():
    title = get_title()
    if title:
        title = title.split('[')[0].split('(')[0].split('/')[0].strip()
        history.add_to_history(title) 
        xbmcgui.Dialog().ok("", "", "Item [" + title + "] add to history")

if __name__ == '__main__':
    main()
