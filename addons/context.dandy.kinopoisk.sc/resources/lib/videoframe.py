import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
import json
import re
import socket
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers

socket.setdefaulttimeout(120)

QUALITY_TYPES = (240, 360, 480, 720, 1080)
PLAYLIST_DOMAIN = "videoframe.online"

def select_season(data):
    tvshow = common.parseDOM(data, "div", attrs={"class": "seasons"})
    seasons = common.parseDOM(tvshow[0], "a")
    values = common.parseDOM(tvshow[0], "a", ret="href")
    if len(seasons) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select season", seasons)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0    
    if index_ < 0:
        return "", ""
    else:
        return values[index_], str(index_+1), str(index_+1)


def select_episode(data, url):
    url_ = url
    sindex = None
    eindex = None
    surl, season, sindex = select_season(data)
    if season == "":
        return "", sindex, eindex

    headers = {
        "Referer": url_,
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }

    try: 
        request = urllib.request.Request("http://" + PLAYLIST_DOMAIN + surl, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib.request.urlopen(request).read()
    except:
        return "", sindex, eindex

    tvshow = common.parseDOM(response, "div", attrs={"class": "items"})
    series = common.parseDOM(tvshow[0], "span")
    evalues = common.parseDOM(tvshow[0], "span", ret="data-num")

    if len(series) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", series)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0  
    episode = str(index_+1)
    eindex = str(index_+1)
    if index_ < 0:
        return "", sindex, eindex

    values = {
        "ep": episode,
    }  
    encoded_kwargs = urllib.parse.urlencode(list(values.items()))
    argStr = "&%s" %(encoded_kwargs)

    try: 
        request = urllib.request.Request("http://" + PLAYLIST_DOMAIN + surl + argStr, "", headers)
        request.get_method = lambda: 'GET'
        return urllib.request.urlopen(request).read(), sindex, eindex
    except:
        return "", sindex, eindex


def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    headers = {
        "Host": "videoframe.online",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    try: 
        request = urllib.request.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib.request.urlopen(request).read()
    except:
        return manifest_links, subtitles, season, episode 

    #tvshow
    tvshow = common.parseDOM(response, "div", attrs={"class": "seasons"})
    if tvshow:
        response, season, episode = select_episode(response, url)
        if response == "":
            return manifest_links, subtitles, season, episode 

    url_ = response.split('url("')[-1].split('")')[0].replace("thumb001.jpg", "hls.m3u8")
    headers = {
        "Host": "cdn.videoframe.online",
        "Origin": "http://videoframe.online",
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    request = urllib.request.Request(url_, "", headers)
    request.get_method = lambda: 'GET'
    try:
        response2 = urllib.request.urlopen(request)
    except urllib.error.HTTPError as error:
        url_ = dict(error.info())['location']

    headers = {
        "Origin": "null",
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    request = urllib.request.Request(url_, "", headers)
    request.get_method = lambda: 'GET'
    try:
        response = urllib.request.urlopen(request).read()
    except:
        return manifest_links, subtitles, season, episode 

    block = url_.replace("hls.m3u8", "")
    urls = re.compile("\.\/.*?\n").findall(response)
    for i, url in enumerate(urls):
        manifest_links[QUALITY_TYPES[i]] = block + url.replace("./", "").replace("\n", "")

    return manifest_links, subtitles, season, episode 
   