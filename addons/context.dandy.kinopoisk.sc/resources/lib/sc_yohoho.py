import sys
import json
import urllib, urllib2
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers
from videohosts import tools

URL = "https://ahoy.yohoho.online/"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://yohoho.cc",
    "Referer": "https://yohoho.cc/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
}

HEADERS2 = {
    "Host": "hdgo.cx",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

VALUES = {
    "kinopoisk": "{0}",
    "tv": "1",
    "resize": "1",
    "player": "videocdn,collaps,iframe,hdvb,kodik",
    "button": "videocdn: {Q} {T}, hdvb: {Q} {T}, kodik: {Q} {T}, iframe: {Q} {T}",
    "button_limit": "8",
    "button_size": "1",
    "separator": ","
}

#ENABLED_HOSTS = ("iframe", "kodik", "videocdn", "hdvb", "collaps")
ENABLED_HOSTS = ("hdvb", "collaps")

_kp_id_ = ''

def prepare_url(host, url):
    if not url:
        return ""
    #response = tools.get_response(url, HEADERS2, {}, 'GET')
    #if response:
    #    return common.parseDOM(response, "iframe", ret="src")[0]
    #else:
    return url

def get_add_info(translate, quality):
    result = ""
    if (not translate):
        translate = ""
    if (not quality):
        quality = ""
    if ((translate != "") or (quality != "")):
        result = "({0})"
    result = result.format((translate if (translate != "") else "") + (("," + quality) if (quality != "") else ""))
    return result

def get_content():
    vh_title = "yohoho."
    list_li = []

    VALUES["kinopoisk"] = _kp_id_
    response = tools.get_response(URL, HEADERS, VALUES, 'POST')

#{"moonwalk":{},
#"hdgo":{},
#"trailer":{},
#"torrent":{},
#"videospider":{},
#"kodik":{},
#"videocdn":{"iframe":"//90.tvmovies.in/kLShoChnGWEE/movie/107","translate":"Полное дублирование","quality":"hddvd"},
#"hdvb":{"iframe":"https://vid1572801764.farsihd.pw/movie/db8f575a1374728dda63eb6244be9bca/iframe","translate":"многоголосый закадровый","quality":"HDRip"},
#"iframe":{"iframe":"https://videoframe.at/movie/42da420pb7p/iframe","translate":"","quality":""},
#"collaps":{"iframe":"https://api1572798262.buildplayer.com/embed/movie/334","translate":"","quality":""}}
    
    if response:
        jdata = json.loads(response)
        for host in ENABLED_HOSTS:
            host_data = jdata[host]
            if host_data:
                iframe = host_data["iframe"]
                translate = host_data["translate"]
                quality = host_data["quality"]
                title_ = "*T*"
                title = "[COLOR=orange][{0}][/COLOR] {1} {2}".format(vh_title + host, tools.encode(title_), get_add_info(translate, quality))
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
