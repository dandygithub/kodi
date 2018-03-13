import sys
import urllib, urllib2
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers

URL = "http://hdnow.biz/api/code"

HEADERS = {
    "Host": "hdnow.biz",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

VALUES = {
    "kp": "{0}",
}

_kp_id_ = ''

def get_response(url, headers, values, method):
    if method == 'GET':
        encoded_kwargs = urllib.urlencode(values.items())
        argStr = ""
        if encoded_kwargs:
            argStr = "?%s" %(encoded_kwargs)
        url2 = url + argStr
      
        request = urllib2.Request(url + argStr, "", headers)
    else:
        request = urllib2.Request(url, urllib.urlencode(values.items()), headers)
    request.get_method = lambda: method
    return urllib2.urlopen(request).read()

def get_content():
    vh_title = "hdnow.biz"
    list_li = []

#    http://czx.to/baza/hdnow.php
#    http://hdnow.biz/content/show/
#    <iframe src='http://hdnow.biz/api/code?kp=1060780' frameborder='0'  width='607' height='360' scrolling='no' allowfullscreen></iframe>

    VALUES["kp"] = _kp_id_
    response = get_response(URL, HEADERS, VALUES, 'GET')
        
    if response:
        iframe = common.parseDOM(response, "iframe", ret="src")[0]
        title_ = ""
        title = "[COLOR=orange][{0}][/COLOR] {1}".format(vh_title, title_)
        uri = sys.argv[0] + "?mode=show&url={0}".format(urllib.quote_plus(iframe))
        item = xbmcgui.ListItem(title)
        list_li.append([uri, item, True]) 
    return list_li


def process(kp_id):
    global _kp_id_
    _kp_id_ = kp_id
    xbmc.log("kp_id=" + kp_id)
    list_li = get_content()
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
