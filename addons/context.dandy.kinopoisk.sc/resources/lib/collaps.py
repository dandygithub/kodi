import urllib, urllib2
import json
import re
import socket
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers
import tools

socket.setdefaulttimeout(120)

QUALITY_TYPES = ("1.LQ", "2.HQ")
PLAYLIST_DOMAIN = "vidozzz.com"

HEADERS = {
    "Referer": "https://yohoho.cc/",    
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

def select_translator_(data, url):
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

#hlsList: {"480":"https://hls-t001-l001-c001-s001.videobalancer.net:15000/07_11_18/07/11/20/6ToUEcIq/1080_PLYZTt00.mp4/tracks/v2-a/master.m3u8","720":"https://hls-t001-l001-c001-s001.videobalancer.net:15000/07_11_18/07/11/20/6ToUEcIq/1080_PLYZTt00.mp4/tracks/v1-a/master.m3u8"},

        
#EXTM3U

#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio0",LANGUAGE="ru",NAME="",AUTOSELECT=YES,DEFAULT=YES,CHANNELS="2",URI="index-a1.m3u8"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio0",LANGUAGE="uk",NAME="",AUTOSELECT=NO,DEFAULT=NO,CHANNELS="2",URI="index-a2.m3u8"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio0",LANGUAGE="en",NAME="Eng.Original",AUTOSELECT=NO,DEFAULT=NO,CHANNELS="2",URI="index-a3.m3u8"

#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=763271,RESOLUTION=1280x544,FRAME-RATE=23.974,CODECS="avc1.640028,mp4a.40.2",VIDEO-RANGE=SDR,AUDIO="audio0"
#index-v1.m3u8

#EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=52611,RESOLUTION=1280x544,CODECS="avc1.640028",URI="iframes-v1.m3u8",VIDEO-RANGE=SDR

def select_translator(data):
    translators = re.compile('NAME=\"(.*?)\"').findall(data)

    if len(translators) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select translator", translators)
        if int(index_) < 0:
            index_ = 0    
    else:
        index_ = 0
    return  index_+1   

def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    try: 
        response = tools.get_response(url, HEADERS, {}, "GET")
    except:
        return manifest_links, subtitles, season, episode 

    hlsList =  response.split("hlsList: {")[-1].split("}")[0].split(",")
    url_ = hlsList[0].split('":"')[1].replace('"', "")
    
    xbmc.log("url_=" + url_)

    try: 
        response = tools.get_response(url_, HEADERS, {}, "GET")
    except:
        return manifest_links, subtitles, season, episode 

    xbmc.log("response_=" + response)

    tr_value = select_translator(response)
    for item in hlsList:
        quality = int(item.split('":"')[0].replace('"', ""))
        url_ = item.split('":"')[1].replace('"', "").replace("master.m3u8", "index-a" + str(tr_value) + ".m3u8")
        xbmc.log("url__=" + url_)        
        manifest_links[quality] = url_
        
    return manifest_links, subtitles, season, episode 
   