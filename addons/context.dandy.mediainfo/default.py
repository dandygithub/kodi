# -*- coding: utf-8 -*-
# Writer (c) 2017, dandy
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcaddon
import xbmcgui
import re
import sys, os
import urllib.request, urllib.parse, urllib.error
import simplejson as json

sys.path.append(os.path.dirname(__file__)+ '/../script.extendedinfo')
sys.path.append(os.path.dirname(__file__)+ '/../script.extendedinfo/lib')
try:
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.urllib3/lib')
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.chardet/lib')
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.certifi/lib')
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.idna/lib')
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.kodi65/lib')
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.requests/lib')
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.youtube.dl/lib')
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.autocompletion/lib')
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.addon.signals/lib')
    sys.path.append(os.path.dirname(__file__)+ '/../script.module.kodi-six/libs')
except:
    pass
import TheMovieDB as tmdb

ID = "context.dandy.mediainfo"
ADDON = xbmcaddon.Addon(ID)

IS_ORIGINALTITLE = ADDON.getSetting('is_originaltitle') if ADDON.getSetting('is_originaltitle') else "true"
IS_EDIT = ADDON.getSetting('is_edit') if ADDON.getSetting('is_edit') else "true"
PATTERNS_FOR_EDIT = ADDON.getSetting('patterns_edit') if ADDON.getSetting('patterns_edit') else ".*"
PATTERNS_FOR_DELETE = ADDON.getSetting('patterns_delete') if ADDON.getSetting('patterns_delete') else "[(].+?[)],[[].+?[]]"
ALWAYS_FROM_TMDB = ADDON.getSetting('always_from_tmdb') if ADDON.getSetting('always_from_tmdb') else "false"
YOUTUBE_MODE = ADDON.getSetting('youtube_mode') if ADDON.getSetting('youtube_mode') else "false"
METALLIQ_MODE = ADDON.getSetting('metalliq_mode') if ADDON.getSetting('metalliq_mode') else "false"

TYPE_MEDIA_INFO = {"tv": "extendedtvinfo", "person": "extendedactorinfo", "movie": "extendedinfo", "none": "extendedinfo"}

_title_ = ""
_year_ = ""
_movie_id_ = ""
_media_type_ = "none"
_iddb_ = ""

def get_title():
    title = xbmc.getInfoLabel("ListItem.OriginalTitle") if xbmc.getInfoLabel("ListItem.OriginalTitle") and IS_ORIGINALTITLE == "true" else None
    if title is None:
       title = xbmc.getInfoLabel("ListItem.Title") if xbmc.getInfoLabel("ListItem.Title") else xbmc.getInfoLabel("ListItem.Label")
    return decode_(title)

def check_is_edit(title):
    isedit = False
    if IS_EDIT == "true":
        patterns = PATTERNS_FOR_EDIT.split(",") if PATTERNS_FOR_EDIT else []
        isedit = False
        for pattern in patterns:
            match = re.compile(decode_(pattern)).match(title)
            if match:
               isedit = True
               break
    return isedit

def edit_title(title):
    if check_is_edit(title) == True:
        kbd = xbmc.Keyboard()
        kbd.setDefault(title)
        kbd.setHeading('Edit title')
        kbd.doModal()
        if kbd.isConfirmed():
            title = kbd.getText().decode('utf8')
        else: 
            title = ""
    return title

def get_media_title():
    title = get_title()
    patterns = PATTERNS_FOR_DELETE.split(",") if PATTERNS_FOR_DELETE else []
    for pattern in patterns:
        title = re.compile(decode_(pattern)).sub("", title).strip()
    #title = title.split("/")[0].strip()
    title = edit_title(title) 
    return title

def get_media_meta_year():
    title = get_title()
    pattern = r"[([]([12][90]\d\d)[]), ]"
    match = re.compile(decode_(pattern)).search(title)
    return match.group(1) if match else ""

def get_attr(data, attr, default):
    return data[attr] if attr in data else default

def get_date_by_tag(item):
    attr = get_attr(item, "release_date", "")
    if attr == "":
        attr = get_attr(item, "first_air_date", "")
    if attr != "":
        attr = attr.split("-")[0]
    return attr

def get_item_title(item):
    title = get_attr(item, "title", "<None>")
    if title == "<None>":
        title = get_attr(item, "name", "<None>")
    return title

def select_dialog_type():
    types = ["Info about Media", "YouTube Videos"]
    if YOUTUBE_MODE == "true":
        ret = xbmcgui.Dialog().select("Select dialog type", types)
        if ret == 1:
            return "youtube"
        else:
            if ret < 0:
                return "none"
            else:
                return "info"
    else:                
        return "info"

def select_process_type():
    types = ["This Add-on", "[COLOR ff0084ff]M[/COLOR]etalli[COLOR ff0084ff]Q[/COLOR]"]
    if (METALLIQ_MODE == "true") and (xbmc.getCondVisibility("System.HasAddon(plugin.video.metalliq)") == True):
        ret = xbmcgui.Dialog().select("Select process type", types)
        if ret == 1:
            return "metalliq"
        else:
            if ret < 0:
                return "none"
            else:
                return "this"
    else:                
        return "this"

def select_media(data):
    global _title_, _year_, _media_type_
    media = []
    for item in data:
        title = get_item_title(item)
        title_orig = get_attr(item, "original_title", title)
        media_type = get_attr(item, "media_type", "movie")
        date = get_date_by_tag(item)
        original_language = get_attr(item, "original_language", "none")
        if media_type == "person":
            media.append("%s [%s]" % (title, media_type))
        else:
            media.append("%s/%s [%s, %s, %s]" % (title, title_orig, date, media_type, original_language))
#tmdb={u'total_results': 1, u'total_pages': 1, u'page': 1, u'results': [{u'poster_path': u'/jB5VQeYO2nr4h31RjXnnER9JoRN.jpg', u'title': u'\u0421\u0444\u0435\u0440\u0430', u'overview': u'\u0424\u0438\u043b\u044c\u043c \u0440\u0430\u0441\u0441\u043a\u0430\u0436\u0435\u0442 \u043e\u0431 \u0438\u043d\u0442\u0435\u0440\u043d\u0435\u0442-\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438 The Circle, \u043e\u0431\u044a\u0435\u0434\u0438\u043d\u044f\u044e\u0449\u0435\u0439 \u0432 \u0435\u0434\u0438\u043d\u0443\u044e \u0441\u0438\u0441\u0442\u0435\u043c\u0443 \u044d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u0443\u044e \u043f\u043e\u0447\u0442\u0443 \u0441\u0432\u043e\u0438\u0445 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439, \u0441\u0442\u0440\u0430\u043d\u0438\u0447\u043a\u0438 \u0432 \u0441\u043e\u0446\u0438\u0430\u043b\u044c\u043d\u044b\u0445 \u0441\u0435\u0442\u044f\u0445, \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044e \u043e \u0431\u0430\u043d\u043a\u043e\u0432\u0441\u043a\u0438\u0445 \u043a\u0430\u0440\u0442\u0430\u0445 \u0438 \u043f\u043e\u043a\u0443\u043f\u043a\u0430\u0445. \u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u043e\u043c \u044d\u0442\u043e\u0433\u043e \u043f\u0440\u043e\u0446\u0435\u0441\u0441\u0430 \u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u0441\u044f \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u0435 \u0447\u0435\u043b\u043e\u0432\u0435\u043a\u043e\u043c \u0443\u043d\u0438\u0432\u0435\u0440\u0441\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u043e\u043d\u043b\u0430\u0439\u043d-\u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u0430. \u041d\u043e \u043d\u0430 \u043f\u0440\u0430\u043a\u0442\u0438\u043a\u0435 \u043d\u0435 \u0432\u0441\u0435 \u0442\u0430\u043a \u0433\u043b\u0430\u0434\u043a\u043e: \u043f\u0440\u043e\u0435\u043a\u0442, \u043f\u043e\u0437\u0438\u0446\u0438\u043e\u043d\u0438\u0440\u0443\u0435\u043c\u044b\u0439 \u043a\u0430\u043a \u043d\u043e\u0432\u0430\u044f \u0441\u0442\u0443\u043f\u0435\u043d\u044c \u0432 \u0440\u0430\u0437\u0432\u0438\u0442\u0438\u0438 \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0439, \u043f\u0440\u0435\u0441\u043b\u0435\u0434\u0443\u0435\u0442 \u0438 \u0434\u0440\u0443\u0433\u0438\u0435, \u0431\u043e\u043b\u0435\u0435 \u0433\u0440\u044f\u0437\u043d\u044b\u0435 \u0446\u0435\u043b\u0438.', u'release_date': u'2017-04-27', u'popularity': 9.357582, u'original_title': u'The Circle', u'backdrop_path': u'/mYpuI61SFcFD9UCkJOLGVxZkIfz.jpg', u'vote_count': 3, u'video': False, u'adult': False, u'vote_average': 0.5, u'original_language': u'en', u'id': 339988, u'genre_ids': [18, 53, 878]}]}
    ret = 0
    if len(media) > 0:
        if len(media) > 1:
            ret = xbmcgui.Dialog().select("Select media", media)
        if ret >= 0:
            _year_ = get_date_by_tag(data[ret])
            _media_type_ = get_attr(data[ret], "media_type", "movie")
            _title_ = get_item_title(data[ret])
            return str(data[ret]["id"])
        else:
            return None
    else:
        return None

def get_media_category():
#    if xbmc.getCondVisibility("Container.Content(tvshows)"):
#        return "tv"
#    else:
    return "multi"

def get_media_meta_movie_id():
    global _year_, _media_type_
    if _title_ == "":
        return ""
    params = {"query": _title_,
              "language": "ru",
              "include_adult": True}
    if _year_ != "":
        params["year"] = int(_year_)
    try:
        response = tmdb.get_data(url="search/%s" % (get_media_category()),
                                 params=params,
                                 cache_days=1)
    except:
        try:
            params = {k: encode_(v) for k, v in params.items() if v}
            xbmc.log("url=" + ("search/%s?%s&" % (get_media_category(), urllib.parse.urlencode(params))))
            response = tmdb.get_tmdb_data(url="search/%s?%s&" % (get_media_category(), urllib.parse.urlencode(params)),
                                          cache_days=1)
            xbmc.log("Response from TMDB = " + repr(response))
        except:
            return None
    
    if response and (not (response == "Empty")):
        if (('status_code'  in response) and (response['status_code'] > 0)):
    	    show_message(response['status_message'])
    	    xbmc.log("status_message=" + repr(response['status_message']))
    	    return None
        elif (('results'  in response) and  len(response['results']) > 0):
            return select_media(response["results"])
        else:
            return None
    else:
        return None

def get_iddb():
    return xbmc.getInfoLabel("ListItem.DBID") if xbmc.getInfoLabel("ListItem.DBID") and (xbmc.getInfoLabel("ListItem.DBID") != "-1") else ""

def get_params():
    params = "info=%s" % (TYPE_MEDIA_INFO[_media_type_])
    if _title_ != "":
        params = params + ",name=%s" % _title_
    if _year_ != "":
        params = params + ",year=%s" % _year_
    if _iddb_  != "":
        params = params + ",dbid=%s" % _iddb_
    if xbmc.getInfoLabel("ListItem.Property(id)") and (_iddb_  == ""):
        params = params + ",id=%s" % xbmc.getInfoLabel("ListItem.Property(id)")
    elif _movie_id_ != "":
        params = params + ",id=%s" % _movie_id_
    return params

def check_params():
    check = True
    add = ""
    if (_iddb_ == ""):
        if _title_ == "":
            check = False
            add = "no title"
        if _movie_id_ == None:
            check = False
            add = "no media"
        if check == False:
            show_message("Error prepare data - " + add)
    return check

def decode_(param):
        return param

def encode_(param):
    try:
        return str(param)
    except:
        return param

def show_message(msg):
    xbmc.executebuiltin("XBMC.Notification(%s, %s, %s)" % ("ERROR", msg, str(5 * 1000)))


def main():
    global _title_, _year_, _movie_id_, _iddb_

    _iddb_ = get_iddb()

    if (_iddb_ == "") or (ALWAYS_FROM_TMDB == "true"):
        _title_ = get_media_title()
        _iddb_ = ""
        _year_ = get_media_meta_year()
    else:
        _title_ = get_title()

    if _title_ == "":
        return
    mode = select_process_type()
    if mode == "none":
        return
    elif mode == "metalliq":
        url = "plugin://plugin.video.metalliq/movies/tmdb/search_term/%s/1" % _title_
        xbmc.executebuiltin("ActivateWindow(videos,%s,return)" % encode_(url))
        return

    mode = select_dialog_type()
    if mode == "none":
        return
    elif mode == "youtube":
        xbmc.executebuiltin("RunScript(script.extendedinfo,info=youtubebrowser,id=%s)" % encode_((decode_(_title_) + " " + _year_ + " " + (_media_type_ if _media_type_ != "none" else "")).strip()))
        return

    _movie_id_ = get_media_meta_movie_id()
    if check_params():
        xbmc.executebuiltin("RunScript(script.extendedinfo,%s)" % encode_(get_params()))

if __name__ == '__main__':
    main()
