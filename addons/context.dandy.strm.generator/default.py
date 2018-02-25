# -*- coding: utf-8 -*-
# Writer (c) 2017, dandy
# Rev. 1.0.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import sys, os
import urllib
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import re
import time
import Translit as translit
import XbmcHelpers

common = XbmcHelpers
translit = translit.Translit()

ID = "context.dandy.strm.generator"
ADDON = xbmcaddon.Addon(ID)
PATH = ADDON.getAddonInfo('path')

PATTERNS_FOR_DELETE = ADDON.getSetting('patterns_delete') if ADDON.getSetting('patterns_delete') else "[(].+?[)],[[].+?[]]"

IS_EDIT = ADDON.getSetting('is_edit') if ADDON.getSetting('is_edit') else "false"
CATEGORIES = ADDON.getSetting('categories') if ADDON.getSetting('categories') else None
DIRECTORY = ADDON.getSetting('directory') if ADDON.getSetting('directory') else PATH
TRANSLIT = ADDON.getSetting('translit') if ADDON.getSetting('translit') else "false"
GENERATE_NFO = ADDON.getSetting('nfo') if ADDON.getSetting('nfo') else "false"
GENERATE_US = ADDON.getSetting('us') if ADDON.getSetting('us') else "false"

_kp_id_ = ''
_media_title_ = ''
_image_ = ''
_addon_id_ = ''

def get_addon_id():
    return xbmc.getInfoLabel('Container.PluginName')

def get_title():
    title = xbmc.getInfoLabel("ListItem.Title") if xbmc.getInfoLabel("ListItem.Title") else xbmc.getInfoLabel("ListItem.Label")
    return decode_(title)

def check_is_edit(title):
    isedit = False
    if IS_EDIT == "true":
        isedit = True
    return isedit

def edit_title(title):
    if check_is_edit(title) == True:
        kbd = xbmc.Keyboard()
        kbd.setDefault(title)
        kbd.setHeading('Edit title')
        kbd.doModal()
        if kbd.isConfirmed():
            title = kbd.getText()
        else: 
            title = ""
    return title

def get_media_title():
    title = get_title()
    year = get_media_year(title)
    patterns = PATTERNS_FOR_DELETE.split(",") if PATTERNS_FOR_DELETE else []
    for pattern in patterns:
        title = re.compile(decode_(pattern)).sub("", title).strip()
    title = title.replace(":", ".")
    if year:
        title = "{0} [{1}]".format(title, year)
    title = edit_title(title) 
    return title

def get_media_year(title):
    pattern = r"[([]([12][90]\d\d)[]), ]"
    match = re.compile(decode_(pattern)).search(title)
    return match.group(1) if match else None

def get_image():
    image = xbmc.getInfoLabel("ListItem.Icon") if xbmc.getInfoLabel("ListItem.Icon") else xbmc.getInfoLabel("ListItem.Thumb")
    return decode_(image)

def select_category():
    category = None
    if CATEGORIES != None:
       ret = xbmcgui.Dialog().select("Select category", CATEGORIES.split(";"))
       if ret >= 0:
           category = CATEGORIES.split(";")[ret]
    return category

def update_uri(content, uri):
    uril = content.split("&uri=")[1].replace("\n", "").split('@')
    uriout = ""
    for item in uril:
        if get_addon_id(item) != get_addon_id(uri):
            uriout = uriout + item + '@'
    uriout = uriout + uri 
    return uriout

def generate_strm(category, media_title):
    if (TRANSLIT == "true") and (GENERATE_US == "false"):
        media_title = translit.eng(media_title)

    path = xbmc.getInfoLabel('ListItem.FileNameAndPath')

    dirlib = os.path.join(DIRECTORY.decode("utf-8"), 'lib/' + category.replace("(ts)", "").strip())
    if not os.path.exists(dirlib):
        os.makedirs(dirlib)

    uri = path
    action = "Generated " 
    if ("(ts)" in category) and (GENERATE_US == "false"):
        namedir = dirlib + "/" + encode_(media_title)
        namefile = dirlib + "/" + encode_(media_title) + "/s1e1.strm"        
        name = namedir
        if not os.path.exists(namedir):
            os.makedirs(namedir)
        else:
            if (xbmcgui.Dialog().yesno(".strm", "", "Exist .strm file. Continue?") == False):
                return
            f = open(namefile, "r+")
            content = urllib.unquote_plus(f.read())
            f.close()
            if (ID in content):
                if (xbmcgui.Dialog().yesno(".strm", "", "Update existing .strm file?") == True):
                    uri = update_uri(content, uri)
                    action = "Updated "                    
        try:
            f = open(namefile, "w+")
            uri = "plugin://{0}?mode=run&uri={1}".format(ID, urllib.quote_plus(uri))
            f.write(uri + "\n")
            f.close()
        except Exception, e:
            xbmc.log( '[%s]: WRITE EXCEPT [%s]' % (ID, e), 4 )
            show_message(e)
            return

    else:
        name = dirlib + "/" + encode_(media_title) + ".strm"    
        if (GENERATE_US == "true"):
            uri = "plugin://plugin.video.united.search/?action=search&keyword={0}".format(encode_(media_title.split('[')[0].split('(')[0].split('/')[0].strip()))
        else:
            if os.path.exists(name): 
                if (xbmcgui.Dialog().yesno(".strm", "", "Exist .strm file. Continue?") == False):
                    return
                f = open(name, "r+")
                content = urllib.unquote_plus(f.read())
                f.close()
                if (ID in content) and (path not in content):
                    if (xbmcgui.Dialog().yesno(".strm", "", "Update existing .strm file?") == True):
                        uri = update_uri(content, uri)
                        action = "Updated "
        try:
            f = open(name, "w+")
            uri = "plugin://{0}?mode=run&uri={1}".format(ID, urllib.quote_plus(uri))
            f.write(uri + "\n")
            f.close()
        except Exception, e:
            xbmc.log( '[%s]: WRITE EXCEPT [%s]' % (ID, e), 4 )
            show_message(e)
            return
    xbmcgui.Dialog().ok(".strm", "", action + name)

def generate_nfo(category, media_title):
    if "(ts)" in category:
        return
    media_title_orig = media_title
    if TRANSLIT == "true":
        media_title = translit.eng(media_title)

    nfo = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
    nfo += '<movie>\n'
    nfo += "    <title>" + encode_(media_title_orig) + "</title>\n"
    if year:
        nfo += "    <year>" + year + "</year>\n"
    nfo += "</movie>\n"

    dirlib = os.path.join(DIRECTORY.decode("utf-8"), 'lib/' + category)
    if not os.path.exists(dirlib):
        os.makedirs(dirlib)
    name = dirlib + "/" + encode_(media_title) + ".nfo"
    if os.path.exists(name) and (xbmcgui.Dialog().yesno(".strm", "", "Exist .nfo file. Continue?") == False):
        return
    try:
        f = open(name, "w+")
        f.write(nfo + "\n")
        f.close()
    except Exception, e:
        xbmc.log( '[%s]: WRITE EXCEPT [%s]' % (ID, e), 4 )
        show_message(e)
        return
    xbmcgui.Dialog().ok(".nfo", "", "Generated " + name)
    
def generate():
    category = select_category()
    if category == None:
        return
    media_title = get_media_title()
    generate_strm(category, media_title)
    if GENERATE_NFO == "true":
        generate_nfo(category, media_title)

def get_addon_id(uri):
    return uri.split('?')[0].replace("plugin://", '').replace('/', '')

def run(uris):
    xbmc.executebuiltin("Playlist.Clear")
    #xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
    cwnd = xbmcgui.getCurrentWindowId()
    
    uri = uris
    uril = uris.split('@')
    titles = []
    for item in uril:
        titles.append(get_addon_id(item))
    ret = 0
    if len(uril) > 0:
        if len(uril) > 1:
            ret = xbmcgui.Dialog().select("Select source", titles)
        if ret >= 0:
            uri = uril[ret]
        else:
            return
    else:
        return

    if (cwnd == 10000): 
        if ("plugin.video.united.search" in uri):
            show_message("Do not run in this mode")
        else:    
            xbmc.executebuiltin("ActivateWindow({0}, {1})".format("videos", uri))
    else:
        xbmc.executebuiltin("Container.Update({0})".format(uri))
    time.sleep(0.1)

def decode_(param):
    try:
        return param.decode('utf-8')
    except:
        return param

def encode_(param):
    try:
        return unicode(param).encode('utf-8')
    except:
        return param

def show_message(msg):
    xbmc.executebuiltin("XBMC.Notification(%s, %s, %s)" % ("ERROR", msg, str(5 * 1000)))

def main():
    mode = None
    if len(sys.argv) > 1:
        PARAMS = common.getParameters(sys.argv[2])
        mode = PARAMS['mode'] if 'mode' in PARAMS else None
        uris = urllib.unquote_plus(PARAMS['uri']) if 'uri' in PARAMS else None

    if (not mode):
        generate()
    elif mode == "run":
        run(uris)

if __name__ == '__main__':
    main()
