import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
import json
import re
import socket
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers
from . import tools

socket.setdefaulttimeout(120)

HEADERS = {
    "Referer": "https://yohoho.cc/",    
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

#https://api1573397878.buildplayer.com/embed/movie/471
#https://api1573397878.buildplayer.com/contents/season/by-franchise/?id=471&host=zombie-film.com-embed

#[{"id":385,"season":1,"name":"","blocked":false},{"id":386,"season":2,"name":"","blocked":false},{"id":387,"season":3,"name":"","blocked":false},{"id":388,"season":4,"name":"","blocked":false},{"id":392,"season":5,"name":"","blocked":false},{"id":3325,"season":6,"name":"","blocked":false}]

def select_season(franchise, url):
    url_ = "https://" + url.split("//")[-1].split("/")[0] + ("/contents/season/by-franchise/?id=%s&host=zombie-film.com-embed" % franchise)
    try:     
        response = tools.get_response(url_, HEADERS, {}, "GET")
    except:
        return None, None
        
    json_data = json.loads(response)
    seasons = []
    values = []    
    for season in json_data:
        seasons.append(str(season["season"]))
        values.append(season["id"])
    if len(seasons) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select season", seasons)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0    
    if index_ < 0:
        return None, None
    else:
        return values[index_], seasons[index_]

#https://api1573397878.buildplayer.com/contents/video/by-season/?id=385&host=zombie-film.com-embed

#[{"id":4483,"poster":{"origin":"https://img.delivembed.cc/movies/video/4/4/8/3/0/0/0/0/0/0/800x450_4483.jpeg?t=1557491106","placeholder":"https://img.delivembed.cc/movies/video/4/4/8/3/0/0/0/0/0/0/800x450_4483.jpeg?t=1557491106",
#"small":"https://img.delivembed.cc/movies/video/4/4/8/3/0/0/0/0/0/0/800x450_4483.jpeg?t=1557491106"},"duration":2476,
#"urlQuality":{"480":"https://hls-t001-l001-c008-s001.videobalancer.net:15000/06_19_18/06/19/04/L2QPEz3U/1080_eRZe0ykM.mp4/tracks/v2-a/master.m3u8","720":"https://hls-t001-l001-c008-s001.videobalancer.net:15000/06_19_18/06/19/04/L2QPEz3U/1080_eRZe0ykM.mp4/tracks/v1-a/master.m3u8"},
#"seasonId":385,"season":1,"episode":"1","episodeName":"","name":"","blocked":false},

def select_episode(franchise, url):
    sindex = None
    eindex = None
    ids, sindex = select_season(franchise, url)
    if not ids:
        return "", sindex, eindex

    url_ = "https://" + url.split("//")[-1].split("/")[0] + ("/contents/video/by-season/?id=%s&host=zombie-film.com-embed" % ids)
    try:     
        response = tools.get_response(url_, HEADERS, {}, "GET")
    except:
        return None, None

    json_data = json.loads(response)
    episodes = []
    values = []
    urls = []
    for episode in json_data:
        episodes.append(episode["name"])
        values.append(episode["episode"])
        urls.append(episode["urlQuality"])
    if len(episode) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", episodes)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0    
    if index_ < 0:
        return "", None, None
    else:
        return str(urls[index_]), sindex, values[index_]


#hlsList: {"480":"https://hls-t001-l001-c001-s001.videobalancer.net:15000/07_11_18/07/11/20/6ToUEcIq/1080_PLYZTt00.mp4/tracks/v2-a/master.m3u8","720":"https://hls-t001-l001-c001-s001.videobalancer.net:15000/07_11_18/07/11/20/6ToUEcIq/1080_PLYZTt00.mp4/tracks/v1-a/master.m3u8"},

        
#EXTM3U

#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio0",LANGUAGE="ru",NAME="",AUTOSELECT=YES,DEFAULT=YES,CHANNELS="2",URI="index-a1.m3u8"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio0",LANGUAGE="uk",NAME="",AUTOSELECT=NO,DEFAULT=NO,CHANNELS="2",URI="index-a2.m3u8"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio0",LANGUAGE="en",NAME="Eng.Original",AUTOSELECT=NO,DEFAULT=NO,CHANNELS="2",URI="index-a3.m3u8"

#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=763271,RESOLUTION=1280x544,FRAME-RATE=23.974,CODECS="avc1.640028,mp4a.40.2",VIDEO-RANGE=SDR,AUDIO="audio0"
#index-v1.m3u8

#EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=52611,RESOLUTION=1280x544,CODECS="avc1.640028",URI="iframes-v1.m3u8",VIDEO-RANGE=SDR

#franchise:  471 ,


def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    hlsList = []

    try: 
        response = tools.get_response(url, HEADERS, {}, "GET")
    except:
        return manifest_links, subtitles, season, episode 

#{u'720': u'https://hls-t001-l001-c008-s001.videobalancer.net:15000/06_19_18/06/19/04/L2QPEz3U/1080_eRZe0ykM.mp4/tracks/v1-a/master.m3u8', u'480': u'https://hls-t001-l001-c008-s001.videobalancer.net:15000/06_19_18/06/19/04/L2QPEz3U/1080_eRZe0ykM.mp4/tracks/v2-a/master.m3u8'}

    try: 
        if "episode:" in response:
            franchise = response.split("franchise:")[-1].split(",")[0].replace(" ", "")
            data, season, episode = select_episode(franchise, url)
            if episode:
                hlsList = data.replace("{", "").replace("}", "").replace("u'", "").replace("':", '":"').split(",")
        else:
            hlsList =  response.split("hlsList: {")[-1].split("}")[0].split(",")

        for item in hlsList:
            quality = int(item.split('":"')[0].replace('"', ""))
            url_ = item.split('":"')[1].replace('"', "").replace("'", "").replace(" ", "")
            manifest_links[quality] = url_
    except:
        if "seasons:" in response:
            seasons = response.split("seasons:")[-1].split("qualityByWidth")[0]
            data, season, episode = select_episode(seasons, url)
            return manifest_links, subtitles, season, episode 
        else:
            url_ = response.split('hls: "')[-1].split('",')[0]
            manifest_links[0] = url_
        
    return manifest_links, subtitles, season, episode 
   