import sys
import urllib, urllib2
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers
from videohosts import tools

URL = "http://czx.to"

HEADERS = {
    "Host": "czx.to",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

VALUES = {
}

_kp_id_ = ''

def get_content():
    vh_title = "czx.to"
    list_li = []

    response = tools.get_response(URL + '/' + str(_kp_id_) + '/', HEADERS, VALUES, 'GET')
        
    if response:
        iframe = common.parseDOM(response, "iframe", ret="src")[0]
        title_ = "*T*"
        title = "[COLOR=orange][{0}][/COLOR] {1}".format(vh_title, tools.encode(title_))
        uri = sys.argv[0] + "?mode=show&url={0}".format(urllib.quote_plus(iframe))
        item = xbmcgui.ListItem(title)
        list_li.append([uri, item, True])
    return list_li

def process(kp_id):
    global _kp_id_
    _kp_id_ = kp_id
    xbmc.log("czx.to:kp_id=" + kp_id)
    list_li = []
    try:
        list_li = get_content()
    except:
    	pass		    
    return list_li
