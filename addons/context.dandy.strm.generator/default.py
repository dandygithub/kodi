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
    patterns = PATTERNS_FOR_DELETE.split(",") if PATTERNS_FOR_DELETE else []
    for pattern in patterns:
        title = re.compile(decode_(pattern)).sub("", title).strip()
    title = title.replace(":", ".")
    title = edit_title(title) 
    return title

def get_media_year():
    title = get_title()
    pattern = r"[([]([12][90]\d\d)[]), ]"
    match = re.compile(decode_(pattern)).search(title)
    return match.group(1) if match else None

def get_image():
    image = xbmc.getInfoLabel("ListItem.Icon") if xbmc.getInfoLabel("ListItem.Icon") else xbmc.getInfoLabel("ListItem.Thumb")
    return decode_(image)

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

def select_category():
    category = None
    if CATEGORIES != None:
       ret = xbmcgui.Dialog().select("Select category", CATEGORIES.split(";"))
       if ret >= 0:
           category = CATEGORIES.split(";")[ret]
    return category

def generate_strm(category, media_title, year):
    if TRANSLIT == "true":
        media_title = translit.eng(media_title)
    if year:
        media_title = "{0} [{1}]".format(media_title, year)

    path = xbmc.getInfoLabel('ListItem.FileNameAndPath')

    dirlib = os.path.join(DIRECTORY.decode("utf-8"), 'lib/' + category)
    if not os.path.exists(dirlib):
        os.makedirs(dirlib)
    name = dirlib + "/" + encode_(media_title) + ".strm"
    f = open(name, "w+")
    uri = "plugin://{0}?mode=run&uri={1}".format(ID, urllib.quote_plus(encode_(path)))
    f.write(uri + "\n")
    f.close()

def generate_nfo(category, media_title, year):
    if TRANSLIT == "true":
        media_title = translit.eng(media_title)
    if year:
        media_title = "{0} [{1}]".format(media_title, year)

    nfo = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
    nfo += '<movie>\n'
    nfo += "    <title>" + encode_(media_title) + "</title>\n"
    if year:
        nfo += "    <year>" + year + "</year>\n"
    nfo += "</movie>\n"

    dirlib = os.path.join(DIRECTORY.decode("utf-8"), 'lib/' + category)
    if not os.path.exists(dirlib):
        os.makedirs(dirlib)
    name = dirlib + "/" + encode_(media_title) + ".nfo"
    f = open(name, "w+")
    f.write(nfo + "\n")
    f.close()
    
def generate():
    category = select_category()
    if category == None:
        return
    media_title = get_media_title()
    year = get_media_year()
    generate_strm(category, media_title, year)
    if GENERATE_NFO == "true":
        generate_nfo(category, media_title, year)

def run(uri):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    xbmc.executebuiltin("Container.Update({0})".format(uri))

def main():
    mode = None
    if len(sys.argv) > 1:
        PARAMS = common.getParameters(sys.argv[2])
        mode = PARAMS['mode'] if 'mode' in PARAMS else None
        uri = urllib.unquote_plus(PARAMS['uri']) if 'uri' in PARAMS else None

    if (not mode):
        generate()
    elif mode == "run":
        run(uri)

if __name__ == '__main__':
    main()
