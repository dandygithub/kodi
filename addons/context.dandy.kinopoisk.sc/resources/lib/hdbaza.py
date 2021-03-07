import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
import json
import re
import socket
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers
from videohosts import tools

socket.setdefaulttimeout(120)

QUALITY_TYPES = ("1.LQ", "2.HQ")
PLAYLIST_DOMAIN = "vidozzz.com"

HEADERS = {
    "Host": PLAYLIST_DOMAIN,
    "Referer": "http://yohoho.cc/",    
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

HEADERS2 = {
    "Origin": "https://" + PLAYLIST_DOMAIN,
     "Referer": "{0}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

VALUES = {
    "snd": "{0}",
    "s": "{1}",
    "e": "{2}"
}

def select_translator(data, url):
    tr_arr = data.split("sounds: [")[-1].split("seasons")[0].replace("\n", "").replace(" ", "").split("],[")
    translators = []
    tr_values = []
    for tr_item in tr_arr:
        translators.append(tr_item.split(",")[1].replace("'", "").replace("]", ""))
        tr_values.append(tr_item.split(",")[0].replace("'", "").replace("[", ""))

    if len(translators) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select translator", translators)
        if int(index_) < 0:
            index_ = 0    
    else:
        index_ = 0    
    tr_value = tr_values[index_]

    VALUES["snd"] = tr_value
    VALUES["s"] = "1"
    VALUES["e"] = "1"
    response = tools.get_response(url, HEADERS, VALUES, "GET")
    return response, tr_value

def select_season(data, value):
    sss = data.split("soundsList: ")[-1].split("selected_options:")[0].replace(' ', '').replace("\n", '').replace("],}", "]}").replace("},}", "}}").replace("'", '"')
    seasonsjson = json.loads(sss[:len(sss)-1])
    seasons = []
    for season in seasonsjson[value]:
        seasons.append(season)
    seasons.sort()
    values = seasons    
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
        return values[index_], str(index_+1)


def select_episode(data, url):
    sindex = None
    eindex = None
    data_, tr_value = select_translator(data, url)
    season, sindex = select_season(data_, tr_value)
    if season == "":
        return "", sindex, eindex

    VALUES["snd"] = tr_value
    VALUES["s"] = season
    VALUES["e"] = "1"
    try:     
        response = tools.get_response(url, HEADERS, VALUES, "GET")
    except:
        return "", sindex, eindex

    sss = response.split("soundsList: ")[-1].split("selected_options:")[0].replace(' ', '').replace("\n", '').replace("],}", "]}").replace("},}", "}}").replace("'", '"')
    seriesjson = json.loads(sss[:len(sss)-1])
    series = []
    
    for episode in seriesjson[tr_value][season]:
        series.append(str(episode))
    evalues = series

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

    VALUES["snd"] = tr_value
    VALUES["s"] = season
    VALUES["e"] = episode
    try:     
        response = tools.get_response(url, HEADERS, VALUES, "GET")
        return response, sindex, eindex        
    except:
        return "", sindex, eindex


def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    try: 
        response = tools.get_response(url, HEADERS, {}, "GET")
    except:
        return manifest_links, subtitles, season, episode 

    #tvshow
    tvshow = response.split("season:")[1].split(",")[0].replace(" ", "")
    if (tvshow != "null"):
        response, season, episode = select_episode(response, url)
        if response == "":
            return manifest_links, subtitles, season, episode 

    part = response.split("hls_master_file_path: '")[-1].split("',")[0]
    url_ = "https://gethdhls.com" + part
    try: 
        response = tools.get_response(url_, HEADERS2, {}, "GET")
    except:
        return manifest_links, subtitles, season, episode 

    urls = re.compile("https:\/\/.*?\.m3u8").findall(response)
    for i, url in enumerate(urls):
        manifest_links[QUALITY_TYPES[i]] = url

    return manifest_links, subtitles, season, episode 
   