import sys
import urllib, urllib2
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers

URL = "http://moonwalk.co/moonwalk/search_as"

HEADERS = {
    "Host": "moonwalk.co",
    "Referer": "http://moonwalk.co/moonwalk/search_as?sq=&kinopoisk_id={0}&search_for=&search_year=&commit=%D0%9D%D0%B0%D0%B9%D1%82%D0%B8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

HEADERS2 = {
    "Referer": "{0}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

VALUES = {
    "sq": "",
    "kinopoisk_id": "{0}",
    "search_for": "",
    "search_year": "",
    "commit": "%D0%9D%D0%B0%D0%B9%D1%82%D0%B8"
}

_kp_id_ = ''

def get_response(url, headers, values):
    encoded_kwargs = urllib.urlencode(values.items())
    argStr = ""
    if encoded_kwargs:
        argStr = "?%s" %(encoded_kwargs)
    request = urllib2.Request(url + argStr, "", headers)
    request.get_method = lambda: 'GET'
    return urllib2.urlopen(request).read()

def prepare_url(url):
    if not url:
        return ""
    HEADERS2["Referer"] = url
    try:
        response = get_response(url, HEADERS2, {})
        return common.parseDOM(response, "iframe", ret="src")[0]
    except:
        return url

def get_content():
    vh_title = "moonwalk.co"
    list_li = []

    VALUES["kinopoisk_id"] = _kp_id_
    HEADERS["Referer"] = HEADERS["Referer"].format(_kp_id_)
    response = get_response(URL, HEADERS, VALUES)

    if response:
        try:
            table = common.parseDOM(response, "table", attrs={"class": "table table-striped"})[0]
            rows = common.parseDOM(table, "tr")

            for row in rows:
                try: 
                    data = common.parseDOM(row, "div", attrs={"class": "copy-iframe-button btn btn-mini btn-info"}, ret = "onclick")[0]
                except:
                    continue
                url = "http:" + prepare_url("http:" + data.split("<iframe src=\\\'")[-1].split("\\\'")[0])
                title_ = common.parseDOM(row, "td")[0] + " (" + common.parseDOM(row, "td")[2] + ", " + common.parseDOM(row, "td")[3] + ", " + common.parseDOM(row, "td")[4] + ")"
                title = "[COLOR=orange][{0}][/COLOR] {1}".format(vh_title, title_)
                uri = sys.argv[0] + "?mode=show&url={0}&title={1}".format(urllib.quote_plus(url), urllib.quote_plus(title))
                item = xbmcgui.ListItem(title)
                list_li.append([uri, item, True]) 
        except:
            pass 

    return list_li


def process(kp_id):
    global _kp_id_
    _kp_id_ = kp_id
    xbmc.log("moonwalk:kp_id=" + kp_id)
    list_li = []
    list_li += get_content()
    return list_li

def encode_(param):
    try:
        return unicode(param).encode('utf-8')
    except:
        return param

def decode_(param):
    try:
        return param.decode('utf-8')
    except:
        return param

def strip_(string):
    return common.stripTags(string)
