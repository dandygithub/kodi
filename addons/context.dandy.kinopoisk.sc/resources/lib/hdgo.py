import urllib, urllib2
import json
import re
import socket
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers

socket.setdefaulttimeout(120)

QUALITY_TYPES = (360, 480, 720, 1080)


def select_season(data):
    tvshow = common.parseDOM(data, "select", attrs={"name": "season"})
    seasons = common.parseDOM(tvshow[0], "option")
    values = common.parseDOM(tvshow[0], "option", ret="value")
    if len(seasons) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select season", seasons)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0    
    if index_ < 0:
        return ""
    else:
        return values[index_], str(index_ + 1)


def select_episode(data, url):
    sindex = None
    eindex = None
    url_ = url.split("?")[0]
    season, sindex = select_season(data)
    if season == "":
        return "", sindex, eindex

    headers = {
        "Referer": url_,
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    values = {
        "season": season
    }  
    encoded_kwargs = urllib.urlencode(values.items())
    argStr = "?%s" %(encoded_kwargs)
    try: 
        request = urllib2.Request(url_ + argStr, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
    except:
        return "", sindex, eindex

    tvshow = common.parseDOM(response, "select", attrs={"name": "episode"})
    series = common.parseDOM(tvshow[0], "option")
    evalues = common.parseDOM(tvshow[0], "option", ret="value")

    if len(series) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", series)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0  
    episode = evalues[index_]
    eindex = str(index_ + 1)
    if index_ < 0:
        return "", sindex, eindex

    values = {
        "season": season,
        "e": episode,
    }  
    encoded_kwargs = urllib.urlencode(values.items())
    argStr = "?%s" %(encoded_kwargs)

    try: 
        request = urllib2.Request(url + argStr, "", headers)
        request.get_method = lambda: 'GET'
        return urllib2.urlopen(request).read(), sindex, eindex
    except:
        return "", sindex, eindex


def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    headers = {
        "Referer": url,
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    try: 
        request = urllib2.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
    except:
        return manifest_links, subtitles, season, episode 

    url_ = common.parseDOM(response, "iframe", ret="src")[0]
    try: 
        request = urllib2.Request(url_, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
    except:
        return manifest_links, subtitles, season, episode 
    iframe = "http:" + common.parseDOM(response, "iframe", ret="src")[0]
    try: 
        request = urllib2.Request(iframe, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
    except:
        return manifest_links, subtitles, season, episode 

    #tvshow
    tvshow = common.parseDOM(response, "select", attrs={"name": "season"})
    if tvshow:
        response, season, episode = select_episode(response, url_)
        if response == "":
            return manifest_links, subtitles, season, episode 

    response = response.split("media: [")[-1].split("]")[0]

    urls = re.compile("http:\/\/.*?[']").findall(response)
    for i, url in enumerate(urls):
        manifest_links[QUALITY_TYPES[i]] = url.replace("'", "") + "|Referer="+url_;

    return manifest_links, subtitles, season, episode 
   