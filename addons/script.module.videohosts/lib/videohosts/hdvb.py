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

HEADERS2 = {
    "Referer": "{0}", 
    "x-csrf-token": "{1}",
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
        return values[index_], str(int(seasons[index_].split(" ")[0]))

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
    xbmc.log('foundEpisodesGetValues='+str(VALUES))
    data_ = common.parseDOM(data, "div", attrs={"id": "tabs"})[0]
    select = common.parseDOM(data, "select", attrs={"id": "episodes"})[0]
    episodes = common.parseDOM(select, "option")
    xbmc.log('foundEpisodes='+str(episodes))
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

    #data = common.parseDOM(response, "div", attrs={"id": "nativeplayer"}, ret="data-config")[0]
    #jdata = json.loads(data)
    #type_content = jdata["type"]

    #tvshow
    #if (type_content == "serial"):
    #    response, season, episode = select_episode(response, url)
    #    if response == "":
    #        return manifest_links, subtitles, season, episode
    #    data = common.parseDOM(response, "div", attrs={"id": "nativeplayer"}, ret="data-config")[0]
    #    jdata = json.loads(data)

    #url_= "https:" + jdata["hls"].replace("\/", "/")

    url_ = "https://" + url.split("https://")[1].split("/")[0]
    file_ = response.split('let playerConfigs = {"file":"~')[1].split('",')[0]
    url_ = url_ + "/playlist/" + file_ + ".txt"
    #let playerConfigs = {"file":"~Ign13TBN3H-uQxLuMfVgeS5YOPAHk$bWS0GjiHsXWXEAwemdq$ITeHgyZJx3cZdOXPk-IIRmCG3X4er9HSCSw$yK7YHEaZB0ZPcCm0haAye1UrcYjd8rB$SO0fmRVP7RJBsDv9OkKVRb5eovRDgXJyOaOqfCPasrpHA8XkDz0fysY5EyLPkh9LfspydgrEITtZUltwtZpvGb13BPq5EV4-ZVpw1XNbB8voghZTdUYFyKtO0aWZHg7QAMli55Q$akEHesQd5dlKrUjzAOtDebYw!!","hls":0,"id":"player-58c0f859e19f05b3330a7b3f05fa8a71","cuid":"58c0f859e19f05b3330a7b3f05fa8a71","key":"mabC4aDYQe9gzALPUqH1B4va5Ate$A7UO9uXRKX0Yhz8p$zoVOdGHQgHUQmmnQ+U","movie":"58c0f859e19f05b3330a7b3f05fa8a71","host":"kinokong.pro","masterId":"260","masterHash":"7aa8008830e2b0fe5afe809c416a82cd","userIp":"134.17.27.106","poster":"","p2p":true,"rek":{"preroll":["https:\/\/aj1907.online\/zNY_gKnZ54xwOJs-q4qJYrgxq9i4e_emtgNUvxOZU136EUm89vOfcZMl1nYY4lLoEYIEltK1nYMDEf4CApBPiCTgrcBGgAkg","https:\/\/aj1907.online\/zSG4y9GEEI5b0WL2_LtawSP_KrgJ65wCZF5gS2RAuxZfg9bxzx_q3d82al_XRqEa6iov3R_tDIbycTfhzPtfnjftE9TjxDwI"],"midroll":[{"time":"25%","url":"https:\/\/aj1907.online\/z3wWm6ZC9P0kqxfkaWAu2dTelAan98GJpGDsaa7rbzeGKtkJNeH4JqN-f9iLc9EfRF8OBfnjgntm6V-nBkPjBWh_sCZ3dLH4"}],"pausebanner":{"key":"bbe8fc89d1b4ec0363fafb361a1f5ab9","script":"https:\/\/aj1907.online\/63c0d7d8.js","show":true},"endtag":{"key":"6c4661276978c9c87d15d0ba61646a8c","script":"https:\/\/aj1907.online\/63c0d7d8.js","conf":{"show_time":60,"skip_time":15,"movie_et":"0","banner_show":true,"banner_time":600}},"pushbanner":[]},"href":"vb17121coramclean.pw","kp":"1115098","uniq_hash":"9e8d563f8ae3b592d4d4e8743ba4399e"};	

    HEADERS2["Referer"] = url
    HEADERS2["x-csrf-token"] = response.split('"key":"')[1].split('",')[0]

    try: 
        response = tools.get_response(url_, HEADERS2, {}, "POST")
    except:
        return manifest_links, subtitles, season, episode 

    url_ = response
    try: 
        response = tools.get_response(url_, HEADERS, {}, "GET")
    except:
        return manifest_links, subtitles, season, episode 

    #EXTM3U
    #EXT-X-VERSION:3
    #EXT-X-STREAM-INF:BANDWIDTH=1023000,RESOLUTION=1746x720
    #hls/720.m3u8
    #EXT-X-STREAM-INF:BANDWIDTH=568000,RESOLUTION=1164x480
    #hls/480.m3u8
    #EXT-X-STREAM-INF:BANDWIDTH=376000,RESOLUTION=872x360
    #hls/360.m3u8
    #EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=400000,RESOLUTION=640x358\n./360/index.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=858x482\n./480/index.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION=1280x718\n./720/index.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1920x1080\n./1080/index.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=12000000,RESOLUTION=3840x2160\n./2160/index.m3u8\n

    #EXTM3U
    #EXT-X-STREAM-INF:BANDWIDTH=400000,RESOLUTION=640x266
    #./360/index.m3u8
    #EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=858x356
    #./480/index.m3u8
    #EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION=1280x532
    #./720/index.m3u8

    block = url_.replace("index.m3u8", "")
    urls = re.compile("hls\/.*?\.m3u8").findall(response)
    if urls:
        for url in urls:
            manifest_links[int(url.split("/")[1].split(".")[0])] = block + url.replace("./", "").replace("\n", "")
    else:
        urls = re.compile("\.\/.*?\n").findall(response)
        for url in urls:
            manifest_links[int(url.split("/")[1])] = block + url.replace("./", "").replace("\n", "")

    return manifest_links, subtitles, season, episode 
   