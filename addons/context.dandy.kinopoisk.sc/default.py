# -*- coding: utf-8 -*-
# Writer (c) 2017, dandy
# Rev. 1.0.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import sys
import urllib
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import re

import resources.lib.search as search

ID = "context.dandy.kinopoisk.sc"
ADDON = xbmcaddon.Addon(ID)

PATTERNS_FOR_DELETE = ADDON.getSetting('patterns_delete') if ADDON.getSetting('patterns_delete') else "[(].+?[)],[[].+?[]]"
#SubString(Container.PluginName, plugin.video.KinoPoisk.ru)
ADDONS_WITH_KINOPOISKID = {"plugin.video.KinoPoisk.ru": r"\?id=(.*)\&"}
IS_EDIT = ADDON.getSetting('is_edit') if ADDON.getSetting('is_edit') else "false"

_kp_id_ = ''
_media_title_ = ''
_image_ = ''
_addon_id_ = ''

def get_kinopoisk_id():
    pattern = None
    try:
        pattern = ADDONS_WITH_KINOPOISKID[_addon_id_]
    except:
        pass
    if pattern:
        data = xbmc.getInfoLabel('ListItem.FileNameAndPath')
        match = re.compile(decode_(pattern)).search(data)
        return match.group(1) if match else ""
    else:
        return None

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
    title = edit_title(title) 
    return title

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


def main():
    global _kp_id_, _media_title_, _image_, _addon_id_
    _addon_id_ = get_addon_id()
    _kp_id_ = get_kinopoisk_id()
    _media_title_ = get_media_title()
    _image_ = get_image()

    if _kp_id_:
        uri = "plugin://{0}?mode=context&kp_id={1}&media_title={2}&image={3}".format(ID, _kp_id_, urllib.quote_plus(encode_(_media_title_)), urllib.quote_plus(encode_(_image_)))
    else:
        uri = "plugin://{0}?mode=context&media_title={1}&image={2}".format(ID, urllib.quote_plus(encode_(_media_title_)), urllib.quote_plus(encode_(_image_)))
    #xbmc.executebuiltin("ActivateWindow(videos,{0},return)".format(uri))
    xbmc.executebuiltin("Container.Update({0})".format(uri))

if __name__ == '__main__':
    main()
