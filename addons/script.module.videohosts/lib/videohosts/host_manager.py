import urllib, urllib2
import json
import re
import socket
import xbmc
import xbmcgui
import xbmcaddon
import XbmcHelpers
common = XbmcHelpers

import collaps
import iframe
import videocdn
import hdvb

socket.setdefaulttimeout(120)

ID = 'script.module.videohosts'
ADDON = xbmcaddon.Addon(ID)

def select_vhost(hm):
    if len(hm) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select videohost", list(hm))
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0
    if index_ == -1:
        return None
    else:    
        return list(hm)[index_]

def get_playlist_by_vhost(vhost, iframe):
    try:
        if vhost == "HDVB":
            return hdvb.get_playlist(iframe)
        elif vhost == "COLLAPS":
            return collaps.get_playlist(iframe)
        elif vhost == "VIDEOCDN":
            return videocdn.get_playlist(iframe)
        elif vhost == "VIDEOFRAME":
            return iframe.get_playlist(iframe)
        else:
            return None, None, None, None
    except:
        return None, None, None, None

def get_playlist(data):
    manifest_links = {}
    iframes_hm = {} 
    subtitles = None
    season = None
    episode = None
    mode = ADDON.getSetting("mode")
    xbmc.log('hm_mode='+ str(mode))
    preferred = ADDON.getSetting("preferred")

    iframes = common.parseDOM(data, "iframe", ret="src")
    
    if (iframes is None or len(iframes)==0):
        iframes = common.parseDOM(data, "iframe", ret="data-src")
    
    for item in iframes:
        if re.search("vid\d+", item):
            iframes_hm["HDVB"] = item
        elif re.search("api\d+", item):
            iframes_hm["COLLAPS"] = item
        elif "kinokong" in item:
            iframes_hm["VIDEOCDN"] = item
        elif "videoframe" in item:
            iframes_hm["VIDEOFRAME"] = item

    xbmc.log("hm=" + repr(iframes_hm))
    if (len(iframes_hm)==0):
        err='no supported hoster found'
        xbmc.log(err)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", err, str(10 * 1000)))
        return None, None, None, None

    if mode == "preferred":
        test = None
        try:
            test = iframes_hm[preferred]
        except:
            pass
        if test:
            return get_playlist_by_vhost(preferred, iframes_hm[preferred])        
        else:
            mode = "auto"

    if mode == "auto":
        for k, v in iframes_hm.items():
            if manifest_links and (len(manifest_links) > 0):
               break 
            manifest_links, subtitles, season, episode = get_playlist_by_vhost(k, v)
    else:
        vhost = select_vhost(iframes_hm)
        if vhost:
            manifest_links, subtitles, season, episode = get_playlist_by_vhost(vhost, iframes_hm[vhost])

    return manifest_links, subtitles, season, episode 
    