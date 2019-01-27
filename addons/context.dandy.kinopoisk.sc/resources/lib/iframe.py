import urllib, urllib2
import json
import re
import socket
import ssl
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers
import tools

socket.setdefaulttimeout(120)

QUALITY_TYPES = (240, 360, 480, 720, 1080)
PLAYLIST_DOMAIN = "videoframe.at"

HEADERS = {
    "Host": PLAYLIST_DOMAIN,
    "Referer": "http://yohoho.cc/",    
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

HEADERS2 = {
    "Host": PLAYLIST_DOMAIN,
    "Origin": "https://" + PLAYLIST_DOMAIN,
    "Referer": "https://" + PLAYLIST_DOMAIN + "/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    "X-REF": "yohoho.cc",
    "Cookie": "__ifzz=yohoho.cc"
    }

HEADERS3 = {
    "Host": "cdn." + PLAYLIST_DOMAIN,
    "Origin": "https://" + PLAYLIST_DOMAIN,
    "Referer": "https://" + PLAYLIST_DOMAIN + "/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }

VALUES = {
    "token": "{0}",
    "type": "{1}"
}

def select_translator(content, url):
    try:
        tr_div = common.parseDOM(content, 'div', attrs={"class": "bar-button pull-right"})[0]
    except:
        return content, url

    translators_ = common.parseDOM(tr_div, 'a')
    translators = common.parseDOM(translators_, 'span')
    tr_values = common.parseDOM(tr_div, 'a', ret="href")

    if len(translators) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select translator", translators)
        if int(index_) < 0:
            index_ = 0    
    else:
        index_ = 0    

    try:
        tr_value = "https://" + PLAYLIST_DOMAIN + tr_values[index_]    
        response = tools.get_response(tr_value, HEADERS, {}, "GET")
    except:
        return content, url

    return response, tr_value

def select_season(data):
    tvshow = common.parseDOM(data, "div", attrs={"class": "bar-button"})[0]
    seasons = common.parseDOM(tvshow, "a")
    values = common.parseDOM(tvshow, "a", ret="href")
    if len(seasons) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select season", seasons)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0    
    if index_ < 0:
        return "", "", ""
    else:
        return "https://" + PLAYLIST_DOMAIN + values[index_], str(index_+1), str(index_+1)

def select_episode(data, url):
    url_ = url
    sindex = None
    eindex = None
    data, url = select_translator(data, url)
    surl, season, sindex = select_season(data)
    if season == "":
        return "", sindex, eindex

    try: 
        response = tools.get_response(surl, HEADERS, {}, "GET")
    except:
        return "", sindex, eindex

    tvshow = common.parseDOM(response, "div", attrs={"class": "bar-button"})[1]
    series = common.parseDOM(tvshow, "a")
    evalues = common.parseDOM(tvshow, "a", ret="href")

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

    try: 
        response = tools.get_response("https://" + PLAYLIST_DOMAIN + evalues[index_], HEADERS, {}, "GET")
        return response, sindex, eindex        
    except:
        return "", sindex, eindex

def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    ssl._create_default_https_context = ssl._create_unverified_context
    try: 
        response = tools.get_response(url, HEADERS, {}, "GET")    
    except:
        return manifest_links, subtitles, season, episode 

    data_type = common.parseDOM(response, "div", attrs={"id": "videoframe"}, ret="data-type")[0]
        
    #tvshow
    if (data_type == "serial"):
        response, season, episode = select_episode(response, url)
        if response == "":
            return manifest_links, subtitles, season, episode 

    data_token = common.parseDOM(response, "div", attrs={"id": "videoframe"}, ret="data-token")[0]

    url_ = "https://" + PLAYLIST_DOMAIN + "/loadvideo"
    VALUES["token"] = data_token
    VALUES["type"] = data_type
    try: 
        response = tools.get_response(url_, HEADERS2, VALUES, "POST")
    except:
        return manifest_links, subtitles, season, episode 

    jdata = json.loads(response)

    try:
        v_id = jdata["show"]["youtube"]["videoId"]
        link = 'plugin://plugin.video.youtube/play/?video_id=' + v_id
        manifest_links["ad"] = link
        return manifest_links, subtitles, season, episode        
    except:
        pass
    
    try:
        url_ = jdata["show"]["links"]["url"]
    except:    
        return manifest_links, subtitles, season, episode 

    try:
        response = tools.get_response(url_, HEADERS3, {}, "GET")
    except urllib2.HTTPError, error:
        url_ = dict(error.info())['location']
        headers = {
            "Host": url_.split("//")[-1].split("/")[0],
            "Origin": "null",
            "Referer": "https://" + PLAYLIST_DOMAIN + "/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
        }
        response = tools.get_response(url_, headers, {}, "GET")

    block = url_.replace("hls.m3u8", "")
    urls = re.compile("\.\/.*?\n").findall(response)
    for i, url in enumerate(urls):
        manifest_links[QUALITY_TYPES[i]] = block + url.replace("./", "").replace("\n", "")

    return manifest_links, subtitles, season, episode 
   