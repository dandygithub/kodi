import urllib, urllib2
import json
import re
import socket
import xbmcgui
from videohosts import moonwalk
import XbmcHelpers
common = XbmcHelpers

socket.setdefaulttimeout(120)

QUALITY_TYPES = (360, 480, 720, 1080)
PLAYLIST_DOMAIN = "moonwalk.cc"
PLAYLIST_DOMAIN2 = "streamblast.cc"

def select_translator(content, url):
    try:
        tr_div = common.parseDOM(content, 'select', attrs={"name": "translator"})[0]
    except:
        return content, url

    translators = common.parseDOM(tr_div, 'option')
    tr_values = common.parseDOM(tr_div, 'option', ret="value")

    if len(translators) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select translator", translators)
        if int(index_) < 0:
            index_ = 0    
    else:
        index_ = 0    
    tr_value = tr_values[index_]

    headers = {
        "Host": "moonwalk.cc",
        "Referer": url,
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }

    url_ =  url.replace(url.split("serial/")[-1].split("/iframe")[0], tr_value)

    request = urllib2.Request(url_, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()
    return response, url_


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
    #data_, url_ = select_translator(data, url)
    sindex = None
    eindex = None
    url_ = url
    season, sindex = select_season(data)
    if season == "":
        return "", sindex, eindex

    headers = {
        "Referer": url
    }
    values = {
        "season": season,
        "episode": "1",
        "nocontrols_translations": ""
    }  

    request = urllib2.Request(url_, urllib.urlencode(values), headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()

    tvshow = common.parseDOM(response, "select", attrs={"name": "episode"})
    series = common.parseDOM(tvshow[0], "option")

    if len(series) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", series)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0  
    episode = str(index_ + 1)
    eindex = str(index_ + 1)
    if episode < 0:
        return "", sindex, eindex

    values = {
        "season": season,
        "episode": episode,
        "nocontrols_translations": ""
    }  
    encoded_kwargs = urllib.urlencode(values.items())
    argStr = "?%s" %(encoded_kwargs)

    headers = {
        "Host": PLAYLIST_DOMAIN,
        "Referer": url + argStr,
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
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
        "Host": PLAYLIST_DOMAIN,
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

    #tvshow
    tvshow = common.parseDOM(response, "select", attrs={"name": "season"})
    if tvshow:
        response, season, episode = select_episode(response, url)
        if response == "":
            return manifest_links, subtitles, season, episode 

    if "var subtitles = JSON.stringify(" in response:
        subtitles = response.split("var subtitles = JSON.stringify(")[-1].split(");")[0]

    ###################################################
    values, attrs = moonwalk.get_access_attrs(response)
    ###################################################

    headers = {
        "Host": PLAYLIST_DOMAIN,
        "Origin": "http://" + PLAYLIST_DOMAIN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
        "Referer": url,
        "X-Requested-With": "XMLHttpRequest",
    }
    headers.update(attrs)

    request = urllib2.Request('http://' + PLAYLIST_DOMAIN + attrs['purl'], urllib.urlencode(values), headers)
    response = urllib2.urlopen(request).read()

    data = json.loads(response.decode('unicode-escape'))
    playlisturl = data['mans']['manifest_m3u8']

    headers = {
        "Host": PLAYLIST_DOMAIN2,
        "Origin": "http://" + PLAYLIST_DOMAIN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    request = urllib2.Request(playlisturl, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()

    urls = re.compile("http:\/\/.*?\n").findall(response)
    for i, url in enumerate(urls):
        manifest_links[QUALITY_TYPES[i]] = url.replace("\n", "")

    return manifest_links, subtitles, season, episode 
   