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

HEADERS = {
    "Referer": "https://yohoho.cc/",    
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

#?e=1&s=6&t=6850beae94e8cad707ed7d1915c8076d9ec50d4f3679b123c9f6ff7c82d1484b&d=yohoho.cc

VALUES = {
    "e": "{0}",
    "s": "{1}",
    "t": "{2}",
    "d": "yohoho.cc"
}

#https://vid1572991019.vb17102bernardjordan.pw/serial/81902f8614966d6d0ea2956d8d362629575649bff87ab573fe32c3873a77cf36/iframe?e=1&s=6&t=6850beae94e8cad707ed7d1915c8076d9ec50d4f3679b123c9f6ff7c82d1484b&d=yohoho.cc

def select_translator(data, url):
    data = common.parseDOM(data, "div", attrs={"id": "tabs"})[0]
    select = common.parseDOM(data, "select", attrs={"id": "translation"})[0]
    translators = common.parseDOM(select, "option")
    tr_values = common.parseDOM(select, "option", ret="value")

    if len(translators) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select translator", translators)
        if int(index_) < 0:
            index_ = 0    
    else:
        index_ = 0    
    tr_value = tr_values[index_]

    VALUES["t"] = tr_value
    VALUES["s"] = "1"
    VALUES["e"] = "1"
    response = tools.get_response(url, HEADERS, VALUES, "GET")
    return response, tr_value

def select_season(data):
    data = common.parseDOM(data, "div", attrs={"id": "tabs"})[0]
    select = common.parseDOM(data, "select", attrs={"id": "seasons"})[0]
    seasons = common.parseDOM(select, "option")
    values = common.parseDOM(select, "option", ret="value")

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
        return values[index_], str(int(seasons[index_].split(" ")[-1]))

def select_episode(data, url):
    sindex = None
    eindex = None
    tr_value=None
    data_, tr_value = select_translator(data, url)

    season, sindex = select_season(data_)
    if season == "":
        return "", sindex, eindex

    VALUES["t"] = tr_value
    VALUES["s"] = season
    VALUES["e"] = "1"
    data_ = tools.get_response(url, HEADERS, VALUES, "GET")
    data_ = common.parseDOM(data, "div", attrs={"id": "tabs"})[0]
    select = common.parseDOM(data, "select", attrs={"id": "episodes"})[0]
    episodes = common.parseDOM(select, "option")
    values = common.parseDOM(select, "option", ret="value")

    if len(episodes) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", episodes)
        if int(index_) < 0:
            index_ = 0    
    else:
        index_ = 0    
    episode = values[index_]
    eindex = str(int(episodes[index_].split(" ")[0]))

    VALUES["t"] = tr_value
    VALUES["s"] = season
    VALUES["e"] = episode
    response = tools.get_response(url, HEADERS, VALUES, "GET")
    return response, season, episode

#<div id="nativeplayer" style="width: 100%!important; height: 100%!important;" 
#data-config='{"ads":{"ads":{"preroll":"https:\/\/aj1907.online\/zi8jz2vgzS5VdvS8_k7DK5APde-qOEqO1AvrzPjV_Ex-Bb8w5tqeqXrSjvWDxekvgkzDka9c9Ql2jmRLk22G8TObTVKcatLI#pre35-20"}},"poster":"","type":"movie","subtitle":[],"volume_control_mouse":1,"href":null,"token":"d4fc15ae4bc1d97f3875f20b82c1921d",
#"hls":"\/\/cdn0.vb17102bernardjordan.pw\/stream2\/cdn0\/4d9196abe14934f23ae825e6e252e865\/MJTMsp1RshGTygnMNRUR2N2MSlnWXZEdMNDZzQWe5MDZzMmdZJTO1R2RWVHZDljekhkSsl1VwYnWtx2cihVT21kejBTW6J1aZRlQtllMVVjTyoFaaRVV3lVbJJjTEJ0aaREaq1kMRlXTEVVP:1572973203:178.125.77.25:41788699eeee01f8aba86db0345d11340bfd576b1667d7a0e04e3fb5dfabdab4\/index.m3u8",
#"logo":{"width":"","height":"","opacity":"","position":"","src":""},"player_type":3,"text_color":null,"control_color":null,"selector_background":null,"overlay_background":null,"play_button_color":null,"track_watching":true}' ></div>

def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    try: 
        response = tools.get_response(url, HEADERS, {}, "GET")
    except:
        return manifest_links, subtitles, season, episode 

    data = common.parseDOM(response, "div", attrs={"id": "nativeplayer"}, ret="data-config")[0]
    jdata = json.loads(data)
    type_content = jdata["type"]

    #tvshow
    if (type_content == "serial"):
        response, season, episode = select_episode(response, url)
        if response == "":
            return manifest_links, subtitles, season, episode
        data = common.parseDOM(response, "div", attrs={"id": "nativeplayer"}, ret="data-config")[0]
        jdata = json.loads(data)

    url_= "https:" + jdata["hls"].replace("\/", "/")
    
    try: 
        response = tools.get_response(url_, HEADERS, {}, "GET")
    except:
        return manifest_links, subtitles, season, episode 

    #EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=400000,RESOLUTION=640x358\n./360/index.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=858x482\n./480/index.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION=1280x718\n./720/index.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1920x1080\n./1080/index.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=12000000,RESOLUTION=3840x2160\n./2160/index.m3u8\n

    block = url_.replace("index.m3u8", "")
    urls = re.compile("\.\/.*?\n").findall(response)
    for url in urls:
        manifest_links[int(url.split("/")[1])] = block + url.replace("./", "").replace("\n", "")

    return manifest_links, subtitles, season, episode 
   