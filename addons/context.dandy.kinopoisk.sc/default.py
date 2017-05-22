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

_kp_id_ = ''
_media_title_ = ''
_image_ = ''

def get_kinopoisk_id():
    data = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    pattern = r"\?id=(.*)\&"
    match = re.compile(decode_(pattern)).search(data)
    return match.group(1) if match else ""

def get_title():
    title = xbmc.getInfoLabel("ListItem.Title") if xbmc.getInfoLabel("ListItem.Title") else xbmc.getInfoLabel("ListItem.Label")
    return decode_(title)

def get_media_title():
    title = get_title()
    patterns = PATTERNS_FOR_DELETE.split(",") if PATTERNS_FOR_DELETE else []
    for pattern in patterns:
        title = re.compile(decode_(pattern)).sub("", title).strip()
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
    global _kp_id_, _media_title_, _image_
    _kp_id_ = get_kinopoisk_id()
    _media_title_ = get_media_title()
    _image_ = get_image()
    uri = "plugin://{0}?mode=context&kp_id={1}&media_title={2}&image={3}".format(ID, _kp_id_, urllib.quote_plus(encode_(_media_title_)), urllib.quote_plus(encode_(_image_)))
    xbmc.executebuiltin("ActivateWindow(videos,{0},return)".format(uri))

if __name__ == '__main__':
    main()
