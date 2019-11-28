# -*- coding: utf-8 -*-
# Writer (c) 2019, dandy
# Rev. 1.0.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

import XbmcHelpers as common

import resources.lib.SearchHistory as history

ID = 'script.module.dandy.search.history'
ADDON = xbmcaddon.Addon(ID)
PATH = ADDON.getAddonInfo('path')
HANDLE = int(sys.argv[1]) if (len(sys.argv) > 1) else None
PARAMS = sys.argv[2] if (len(sys.argv) > 2) else None
ICON = ADDON.getAddonInfo('icon')

def list_items():
    words = history.get_history()
    for word in reversed(words):
        uri = "plugin://plugin.video.united.search/?action=search&keyword=%s" % word
        item = xbmcgui.ListItem(word, iconImage=ICON, thumbnailImage=ICON)

        commands = []
        uricmd = sys.argv[0] + '?mode=delete&keyword=%s' % word
        commands.append(("[COLOR=orange]Delete[/COLOR] item", "Container.Update(%s)" % (uricmd), ))
        item.addContextMenuItems(commands)

        xbmcplugin.addDirectoryItem(HANDLE, uri, item, False)
    xbmcplugin.endOfDirectory(HANDLE, True)

def search_by_us(keyword):
    uricmd = "plugin://plugin.video.united.search/?action=search&keyword=%s" % keyword
    xbmc.executebuiltin("ActivateWindow(videos,%s)" % uricmd)
    #xbmc.executebuiltin("Container.Update(%s)" % uricmd)

def delete_item(keyword):
    words = history.delete_from_history(keyword)

def main():
    params = common.getParameters(PARAMS)
    mode = params['mode'] if 'mode' in params else None
    keyword = params['keyword'] if 'keyword' in params else None
    if (mode == "search"):
       search_by_us(keyword)
    if (mode == "delete"):
       delete_item(keyword)
    elif (mode is None):
       list_items()

if __name__ == '__main__':
    main()
