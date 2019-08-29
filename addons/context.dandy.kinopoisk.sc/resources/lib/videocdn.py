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

PLAYLIST_DOMAIN = "videocdn.so"

HEADERS = {
    "Referer": "http://yohoho.cc/",    
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

def select_translator(data):
    try:
        div = common.parseDOM(data, "div", attrs={"class": "translations"})[0]
    except:
        try:
            val = common.parseDOM(data, "input", attrs={"id": "translation_id"}, ret="value")[0]
            return val 
        except:
            return "-1"
    translators = common.parseDOM(div, "option")
    tr_values = common.parseDOM(div, "option", ret="value")

    if len(translators) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select translator", translators)
        if int(index_) < 0:
            index_ = 0    
    else:
        index_ = 0    
    tr_value = tr_values[index_]
    return tr_value

def select_season(data):
    seasons = []
    seasons_full = []
    
    for season in data:
        seasons.append(season["comment"])
        seasons_full.append(season)        

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
#        seasons[index_].split(" ")[0]
        return seasons[index_], str(index_+1), seasons_full[index_]

def select_episode(data, tr_value):
    sindex = None
    eindex = None

    links_tr = data[tr_value]

    season, sindex, season_full = select_season(links_tr)
    if season == "":
        return [], sindex, eindex

    series = []
    series_full = []
    
    for seria in season_full["folder"]:
        series.append(seria["comment"])
        series_full.append(seria)
        
    if len(series) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", series)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0  
    if index_ < 0:
        return [], sindex, eindex
    episode = series[index_]
    #eindex = series[index_].split(" ")[0]
    eindex = str(index_)
    links_tr = series_full[index_]["file"].split(',')[-1].split(" or ")

    return links_tr, sindex, eindex

#<input type="hidden" id="files" value="{&quot;6&quot;:&quot;[240p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/240.mp4,[360p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/240.mp4,[480p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/480.mp4 or [360p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/240.mp4,[720p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/480.mp4 or [480p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/480.mp4 or [360p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/movies\/d7d9f08b1ab6c2fd284bed7c887a669cbdb3e112\/bfba6851634fec7e31cd8766d4629066:2019051318\/240.mp4&quot;,&quot;381&quot;:&quot;[240p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/240.mp4,[360p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/240.mp4,[480p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/480.mp4 or [360p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/240.mp4,[720p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/480.mp4 or [480p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/480.mp4 or [360p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/movies\/976c3e57ad81eaedd83353e3743db5d70ece0200\/d027ef6f83047c7046513731de9acd8b:2019051318\/240.mp4&quot;,&quot;2&quot;:&quot;[240p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/240.mp4,[360p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/240.mp4,[480p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/480.mp4 or [360p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/240.mp4,[720p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/480.mp4 or [480p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/480.mp4 or [360p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/movies\/fac28beba1016cde112062c8d02f374d29533ef7\/7680e6cec99264786394a306daa09d00:2019051318\/240.mp4&quot;}">

#<input type="hidden" id="videoType" value="tv_series">

#<input type="hidden" id="files" value="{&quot;10&quot;:[{&quot;id&quot;:1,&quot;comment&quot;:&quot;1 \u0441\u0435\u0437\u043e\u043d&quot;,&quot;folder&quot;:[{&quot;id&quot;:&quot;1_1&quot;,&quot;comment&quot;:&quot;1 \u0441\u0435\u0440\u0438\u044f&lt;br&gt;&lt;i&gt;LostFilm&lt;\/i&gt;&quot;,&quot;file&quot;:&quot;[240p]\/\/cloud.videocdn.ca\/tvseries\/ddc516bcb953e8f3cbb37da0dc419a0e381e06e6\/b2801ce47a220c7a1ef1d498a546b56b:2019051518\/240.mp4,[360p]\/\/cloud.videocdn.ca\/tvseries\/ddc516bcb953e8f3cbb37da0dc419a0e381e06e6\/b2801ce47a220c7a1ef1d498a546b56b:2019051518\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/tvseries\/ddc516bcb953e8f3cbb37da0dc419a0e381e06e6\/b2801ce47a220c7a1ef1d498a546b56b:2019051518\/240.mp4,[480p]\/\/cloud.videocdn.ca\/tvseries\/ddc516bcb953e8f3cbb37da0dc419a0e381e06e6\/b2801ce47a220c7a1ef1d498a546b56b:2019051518\/480.mp4 or [360p]\/\/cloud.videocdn.ca\/tvseries\/ddc516bcb953e8f3cbb37da0dc419a0e381e06e6\/b2801ce47a220c7a1ef1d498a546b56b:2019051518\/360.mp4 or [240p]\/\/cloud.videocdn.ca\/tvseries\/ddc516bcb953e8f3cbb37da0dc419a0e381e06e6\/b2801ce47a220c7a1ef1d498a546b56b:2019051518\/240.mp4,[720p]\/\/cloud.videocdn.ca\/tvseries\/ddc516bcb953e8f3cbb37da0dc419a0e381e06e6\/b2801ce47a220c7a1ef1d498a546b56b:2019051518\/480.mp4 or [480p]\/\/cloud.videocdn.ca\/tvseries\/ddc516bcb953e8f3cbb37da0dc419a0e381e06e6\/b2801ce47a220c7a1ef1d498a546b56b:2019051518\/480.mp4 or [360p]\/\/cloud.videocdn.ca\/tvseries\/ddc516bcb953e8f3cbb37da0dc419a0e381e06e6\/b2801ce47a220c7a1ef1d498a546b56b:2019051518\/360.mp4 or     

def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    try: 
        response = tools.get_response("https:" + url, HEADERS, {}, "GET")
    except:
        return manifest_links, subtitles, season, episode 

    tr_value = select_translator(response)

    links_ = replace_(common.parseDOM(response, "input", attrs={"id": "files"}, ret="value")[0])
    links = json.loads(links_)
  
    #tvshow
    videoType = common.parseDOM(response, "input", attrs={"id": "videoType"}, ret="value")[0]
    if (videoType == "tv_series"):
       links_tr, season, episode = select_episode(links, tr_value)
    else:   
       links_tr = links[tr_value].split(',')[-1].split(" or ")

    for link in links_tr:
        if (not ("p]" in link)):
            manifest_links[link.split("/")[-1].split(".")[0]] = link

    return manifest_links, subtitles, season, episode 

def replace_(data):
    return data.replace("&quot;", '"').replace("\/\/", "https://").replace("\/", "/").replace("&lt;br&gt;", " ").replace("&lt;i&gt;", "(").replace("&lt;/i&gt;", ")")
    