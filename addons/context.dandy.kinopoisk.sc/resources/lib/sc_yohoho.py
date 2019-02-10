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
    "player": "moonwalk,hdgo,iframe,hdbaza,kodik,trailer,torrent",
    "button": "moonwalk: {Q} {T}, hdgo: {Q} {T}, hdbaza: {Q} {T}, kodik: {Q} {T}, iframe: {Q} {T}"
}

ENABLED_HOSTS = ("iframe", "kodik", "moonwalk", "hdgo", "hdbaza")

_kp_id_ = ''

def prepare_url(host, url):
    if not url:
        return ""
    if host != "hdgo":
        return url
    response = tools.get_response(url, HEADERS2, {}, 'GET')
    if response:
        return common.parseDOM(response, "iframe", ret="src")[0]
    else:
        return url

def get_content():
    vh_title = "yohoho."
    list_li = []

    VALUES["kinopoisk"] = _kp_id_
    response = tools.get_response(URL, HEADERS, VALUES, 'POST')
    
    if response:
        jdata = json.loads(response)
        for host in ENABLED_HOSTS:
            host_data = jdata[host]
            if host_data:
                iframe = host_data["iframe"]
                translate = host_data["translate"]
                quality = host_data["quality"]
            
#{"vodlocker":{},
#  "hdgo":{"iframe":"https://hdgo.cx/video/oSlSCtQ0t8apv6vJGD1va2xbKTd9k8YC/17223/","translate":"Дублированный","quality":"плохое TS"},
#  "iframe":{"iframe":"https://videoframe.at/movie/2eb6408pc8p/iframe","translate":"Полное дублирование","quality":"TS"},
#  "torrent":{"iframe":"https://4h0y.yohoho.cc/?title=%D1%85%D0%B8%D1%89%D0%BD%D0%B8%D0%BA"},
#  "hdbaza":{"iframe":"https://vidozzz.com/iframe?mh=bbd8ed61c2256ea4&uh=65bd8ef1126daa6f","translate":"Viruseproject","quality":""},
#  "kodik":{"iframe":"https://kodik.cc/video/15298/6f7fcc06b4e7d51f4ff574af5a59115e/720p","translate":"Проф. Многоголосый","quality":"BDRip 720p"},
#  "trailer":{"iframe":"https://hdgo.cx/video/trailer/oSlSCtQ0t8apv6vJGD1va2xbKTd9k8YC/17223/"},
#  "moonwalk":{"iframe":"https://streamguard.cc/video/d9419273b3fea0ef15980f70e35cc078/iframe?show_translations=1","translate":"Дубляж","quality":""}}
        
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
