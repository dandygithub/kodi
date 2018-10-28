import sys
import urllib, urllib2
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers
import tools

URL = "http://hdgo.club"
PARTS = ("/films/", "/serials/")

HEADERS = {
     "Origin": "http://hdgo.club",
    "Host": "hdgo.club",
    "Referer": "{0}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

HEADERS2 = {
    "Host": "hdgo.club",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

VALUES = {
    "search": "{0}",
    "type": "4",
    "process": "%D0%98%D1%81%D0%BA%D0%B0%D1%82%D1%8C"
}

_kp_id_ = ''

def prepare_url(url):
    if not url:
        return ""
    response = tools.get_response(url, HEADERS2, {}, 'GET')
    if response:
        return "http:" + common.parseDOM(response, "iframe", ret="src")[0]
    else:
        return url

def add_title_info(info):
    result = ""
    if info[2] or info[3]:
        result = " ("
    if info[2]:
        result = result + tools.strip(info[2])
    if info[3]:
        result = result + ", " + tools.strip(info[3])
    if result != "":
        result = result + ")"
    return result

def get_content(part):
    vh_title = "hdgo.club"
    list_li = []

    VALUES["search"] = _kp_id_
    HEADERS["Referer"] = URL + part
    response = get_response(URL + part, HEADERS, VALUES, 'POST')

    if response:
        try:
            arr = common.parseDOM(response, "div", attrs={"class": "li_gen"})
            for item in arr:
                try: 
                    divs = common.parseDOM(item, "div")
                    url_ = "http:" + common.parseDOM(item, "a", attrs={"class": "btn-primary"}, ret="href")[0]
                except:
                    continue
                url = prepare_url(url_)
                title_ = tools.strip(divs[1].split("\n")[0]) + add_title_info(divs)
                title = "[COLOR=orange][{0}][/COLOR] {1}".format(vh_title, tools.encode(title_))
                uri = sys.argv[0] + "?mode=show&url={0}&title={1}".format(urllib.quote_plus(url), urllib.quote_plus(title))
                item = xbmcgui.ListItem(title)
                list_li.append([uri, item, True]) 
        except:
            pass 

    return list_li


def process(kp_id):
    global _kp_id_
    _kp_id_ = kp_id
    xbmc.log("hdgo:kp_id=" + kp_id)
    list_li = []
    for part in PARTS:
        list_li += get_content(part)
    return list_li
