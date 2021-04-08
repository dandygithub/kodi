#!/usr/bin/python
# Writer (c) 2012-2021, MrStealth, dandy
# -*- coding: utf-8 -*-
# License: GPLv3

import xbmc
import xbmcaddon
import xbmcplugin
from lib.MyFavorites import MyFavorites

ID = "script.module.favorites"
ADDON = xbmcaddon.Addon(ID)
PATH = ADDON.getAddonInfo('path')
HANDLE = int(sys.argv[1]) if (len(sys.argv) > 1) else None
PARAMS = sys.argv[2] if (len(sys.argv) > 2) else None
ICON = ADDON.getAddonInfo('icon')

def main():
  if HANDLE:
    favorites = MyFavorites(None)
    favorites.listEx()

if __name__ == '__main__':
    main()
