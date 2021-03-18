#!/usr/bin/python
# Writer (c) 2012-2021, MrStealth, dandy
# License: GPLv3

import urllib.request, urllib.parse, urllib.error

import xbmc
import xbmcaddon

import XbmcHelpers
common = XbmcHelpers

icon = xbmcaddon.Addon('script.module.favorites').getAddonInfo('icon')
language = xbmcaddon.Addon('script.module.favorites').getLocalizedString
title = language(1000)

params = dict([(k, urllib.parse.unquote_plus(v)) for k,v in list(common.getParameters(sys.argv[1]).items())])

from .MyFavorites import MyFavoritesDB
database = MyFavoritesDB(params['plugin'], True)

if params['action'] == "add":
    message = language(1003)

    xbmc.executebuiltin("Notification(%s,%s,%s,%s)" % (title, message, '3000', icon))
    database.save(params['title'], params['url'], params['image'], params['playable'] == 'True')
else:
    message = language(1004)

    xbmc.executebuiltin("Notification(%s,%s,%s,%s)" % (title, message, '3000', icon))
    database.remove(params['title'])

    xbmc.executebuiltin("Container.Refresh")


