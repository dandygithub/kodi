import sys
import urllib, urllib2
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers

URL = "https://videoframe.online/"

HEADERS = {
    "Host": "videoframe.online",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
}

HEADERS2 = {
    "Host": "videoframe.online",
    "Referer": "{0}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

VALUES = {
    "kp_id": "{0}",
}

_kp_id_ = ''

def get_response(url, headers, values, method):
    url2 = url
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
    return url2, urllib2.urlopen(request).read()

# https://videoframe.online/stats.php?y=RFVrDa1_U9k&id=107&t=6&c=0&type=sid&k=MTc4LjEyNS4yMDA%3D&key=2rQr60vwcCKSYIIipQke59SyTTnvQdIBnEUmPFkZm5c%3D

#<body>
#<div data-cost='0' data-key='$12648469544403,$13620057409336,$10776603015633, $15589974089613' data-keyboard='true' class='minimalist flowplayer is-paused is-splash play-button' id='play' data-embed='false' data-translate='6' data-st='MTc4LjEyNS4yMDA=' data-sid='107' data-valid='2rQr60vwcCKSYIIipQke59SyTTnvQdIBnEUmPFkZm5c=' 
#				style='background-image: url("https://cdn.videoframe.online/movies/91530f5b44c5786b810be8a79b144b0ae2537796/9a739e9b642c5d67618cf17e8e91e460:2017111822/thumb001.jpg");'>
#	<div class='paused' id='paused'></div>
#</div>
#<div class='col-lg-12 col-md-12 col-sm-12 col-xs-12 film_title'>Форсаж</div>
#<div class='translate'><div class='trans'>Профессиональный (многоголосый закадровый)</div></div>
#<script>$(function(){$("#play").click(function(){$(this).preRoll({timer:30, hardTimer:15,pre:{youtube:{videoId:"RFVrDa1_U9k",autoplay:false}}})})});</script>
#</body>

def getValues(content):
    values = {}
    values["y"] =  content.split('{videoId:"')[-1].split('",')[0]
    values["id"] = content.split("data-sid='")[-1].split("'")[0]
    values["t"]  = content.split("data-translate='")[-1].split("'")[0]
    values["c"] = content.split("data-cost='")[-1].split("'")[0]
    values["type"] = "sid"
    values["k"] = content.split("data-st='")[-1].split("'")[0]
    values["key"] = content.split("data-valid='")[-1].split("'")[0]
    return values

def getTitle(content):
    title_ = common.parseDOM(content, "div", attrs={"class": "col-lg-12 col-md-12 col-sm-12 col-xs-12 film_title"})[0]
    trans_ = common.parseDOM(content, "div", attrs={"class": "trans"})
    if trans_:
        title_ = title_ + " (" + trans_[0] + ")" 
    return strip_(title_)

def get_content():
    vh_title = "videoframe.online"
    list_li = []

    VALUES["kp_id"] = _kp_id_
    try:
        url2, response = get_response(URL, HEADERS, VALUES, 'GET')
        if response:
            if (not ("Sorry, not found" in response)):
#        values2 = getValues(response) 
#        HEADERS2["Referer"]  = url2
#        url2, response2 = get_response(URL+"stats.php", HEADERS2, values2, 'GET')
#        if response2:
#        url = response2.split('"url":"')[-1].split('","')[0].replace("\/", "/")
                title_ = getTitle(response)
                title = "[COLOR=orange][{0}][/COLOR] {1}".format(vh_title, title_)
                uri = sys.argv[0] + "?mode=show&url={0}&title={1}".format(urllib.quote_plus(url2), urllib.quote_plus(title))
                item = xbmcgui.ListItem(title)
                list_li.append([uri, item, True]) 
    except:
        pass
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
