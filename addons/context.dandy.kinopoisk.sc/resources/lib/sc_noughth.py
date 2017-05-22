import sys
import urllib, urllib2
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers

URL = "https://noughth.ru"
VIDEOHOSTS = ("/API/moonwalk.php", "/API/hdgo.php", "/API/kodik.php", "/API/videoframe.php")

HEADERS = {
    "referer": "https://noughth.ru/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

HEADERS2 = {
    "host": "i.noughth.ru",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

VALUES = {
    "ID": "{0}"
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
    response = get_response(url, HEADERS2, {})
    if response:
        return common.parseDOM(response, "iframe", ret="src")[0]
    else:
        return url

def get_content(videohost):
    vh_title = videohost.split("/API/")[-1].split(".php")[0]
    list_li = []

    VALUES["ID"] = _kp_id_
    response = get_response(URL + videohost, HEADERS, VALUES)

    if response:
        rows = common.parseDOM(response, "tr")
        for row in rows:
            translator = strip_(common.parseDOM(row, "td")[1])
            url = prepare_url(common.parseDOM(row, "a", ret="href")[0])
            if url != 'http://i.noughth.ru/?':
                title = "[COLOR=orange][{0}][/COLOR] {1}".format(vh_title, encode_(translator))
                uri = sys.argv[0] + "?mode=show&url={0}&title={1}".format(urllib.quote_plus(url), urllib.quote_plus(title))
                item = xbmcgui.ListItem(title)
                list_li.append([uri, item, True]) 

    return list_li


def process(kp_id):
    global _kp_id_
    _kp_id_ = kp_id
    list_li = []
    for videohost in VIDEOHOSTS:
        list_li += get_content(videohost)
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
