import sys
import urllib, urllib2
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers
from videohosts import tools

URL = "http://kodik.top"
PARTS = ("/films/", "/serials/")

HEADERS = {
     "Origin": "http://kodik.top",
    "Host": "kodik.top",
    "Referer": "{0}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

HEADERS2 = {
    "Host": "kodik.top",
    "Referer": "{0}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

VALUES = {
    "search": "{0}",
    "type": "4",
}

_kp_id_ = ''

def prepare_url(url):
    if not url:
        return ""
    HEADERS2["Referer"] = url
    response = tools.get_response(url, HEADERS2, {}, 'GET')
    if response:
        return common.parseDOM(response, "iframe", ret="src")[0]
    else:
        return url

def get_content(part):
    vh_title = "kodik.top"
    list_li = []

    VALUES["search"] = _kp_id_
    HEADERS["Referer"] = URL + part
    response = tools.get_response(URL + part, HEADERS, VALUES, 'POST')

    if response:
        try:
            table = common.parseDOM(response, "table", attrs={"class": "table table-hover"})
            tbody = common.parseDOM(table, "tbody")
            rows = common.parseDOM(tbody, "tr") 
            for item in rows:
                try: 
                    tds = common.parseDOM(item, "td")
                    url_ = "https:" + common.parseDOM(item, "a", attrs={"class": "btn btn-success btn-xs copypreview"}, ret="data-link")[0]
                except:
                    continue
                url = prepare_url(url_)
                title_ = tools.strip(tds[0]) + " (" + tools.strip(tds[1]) + ", " + tools.strip(tds[2]) + ")"
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
    xbmc.log("kodik:kp_id=" + kp_id)
    list_li = []
    for part in PARTS:
        list_li += get_content(part)
    return list_li
    