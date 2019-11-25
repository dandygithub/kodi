# -*- coding: utf-8 -*-
# Writer (c) 2019, dandy
# Rev. 1.0.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import sys
import xbmcaddon

ID = 'script.module.dandy.search.history'
ADDON = xbmcaddon.Addon(ID)
HANDLE = int(sys.argv[1]) if (len(sys.argv) > 1) else None
PARAMS = sys.argv[2] if (len(sys.argv) > 2) else None
PATH = ADDON.getAddonInfo('path')

def get_history():
        words = []
        history = ADDON.getSetting('history')
        if history:
        	words = history.split(",")
        return words

def clean():
    ADDON.setSetting('history', '')

def add_to_history(keyword):
    words = []
    history = ADDON.getSetting('history')
    if history:
        words = history.split(",")
    if keyword and keyword not in words:
        words.append(keyword)
        ADDON.setSetting('history', ','.join(words))

def delete_from_history(keyword):
    words = []
    history = ADDON.getSetting('history')
    if history:
        words = history.split(",")
        if keyword and keyword in words:
            words.delete(keyword)
            ADDON.setSetting('history', ','.join(words))
