import sys
import json
import urllib, urllib2
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers
import tools

URL = "https://4h0y.yohoho.cc/"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "http://yohoho.cc",
    "Referer": "http://yohoho.cc/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
}

HEADERS2 = {
    "Host": "hdgo.cx",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

VALUES = {
    "kinopoisk": "{0}",
    "tv": "1",
    "player": "moonwalk,hdgo,kodik,iframe,videocdn,trailer,torrent",
    "button": "moonwalk: {Q} {T}, hdgo: {Q} {T}, kodik: {Q} {T}, iframe: {Q} {T}, videocdn: {Q} {T}",
    "button_limit": "8",
    "button_size": "1",
    "separator": ","
}

ENABLED_HOSTS = ("iframe", "kodik", "moonwalk", "hdgo", "videocdn")

_kp_id_ = ''

def prepare_url(host, url):
    if not url:
        return ""
    #response = tools.get_response(url, HEADERS2, {}, 'GET')
    #if response:
    #    return common.parseDOM(response, "iframe", ret="src")[0]
    #else:
    return url

def get_content():
    vh_title = "yohoho."
    list_li = []

    VALUES["kinopoisk"] = _kp_id_
    response = tools.get_response(URL, HEADERS, VALUES, 'POST')

#{"trailer":{"iframe":"https://trailerclub.me/video/d813512bacc126a4/iframe"},
#  "torrent":{},
#  "vodlocker":{},
#  "iframe":{"iframe":"https://videoframe.at/movie/42da420pc8p/iframe","translate":"Полное дублирование","quality":"BD"},
#  "moonwalk":{"iframe":"https://streamguard.cc/video/09e73f024975678b77004c843fa9cf47/iframe?show_translations=1","translate":"Многоголосый закадровый","quality":""},
#  "kodik":{"iframe":"//kodik.info/video/32562/8e89db0bc47b2f47cf2600c629c4c731/720p","translate":"Дублированный","quality":"BDRip 720p"},
#  "hdgo":{"iframe":"https://vio.to/video/oSlSCtQ0t8apv6vJGD1va2xbKTd9k8YC/5614/","translate":"Профессиональный многоголосый","quality":"хорошее HD"},
#  "videocdn":{"iframe":"//4.videocdn.so/kLShoChnGWEE/movie/107","translate":"Профессиональный (многоголосый закадровый)","quality":"hddvd"}}            
    
    if response:
        jdata = json.loads(response)
        for host in ENABLED_HOSTS:
            host_data = jdata[host]
            if host_data:
                iframe = host_data["iframe"]
                translate = host_data["translate"]
                quality = host_data["quality"]
                title_ = "*T*"
                title = "[COLOR=orange][{0}][/COLOR] {1} ({2})".format(vh_title + host, tools.encode(title_), translate + "," + quality)
                uri = sys.argv[0] + "?mode=show&url={0}".format(urllib.quote_plus(prepare_url(host, iframe)))
                item = xbmcgui.ListItem(title)
                list_li.append([uri, item, True]) 
    return list_li


def process(kp_id):
    global _kp_id_
    _kp_id_ = kp_id
    xbmc.log("yohoho:kp_id=" + kp_id)
    list_li = []
    try:
        list_li = get_content()
    except:
        pass		    
    return list_li
