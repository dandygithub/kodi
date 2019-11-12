import urllib, urllib2
import json
import re
import socket
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers

import collaps
import iframe
import videocdn
import hdvb

socket.setdefaulttimeout(120)

def get_playlist(data):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    iframes = common.parseDOM(data, "iframe", ret="src")
    for item in iframes:
        if (len(manifest_links) > 0):
            break 

        if re.search("vid\d+", item):
            manifest_links, subtitles, season, episode = hdvb.get_playlist(item)
        elif re.search("api\d+", item):
            manifest_links, subtitles, season, episode = collaps.get_playlist(item)
        elif "videocdn" in item:
            manifest_links, subtitles, season, episode = videocdn.get_playlist(item)
        elif "videoframe" in item:
            manifest_links, subtitles, season, episode = iframe.get_playlist(item)

    return manifest_links, subtitles, season, episode 
    