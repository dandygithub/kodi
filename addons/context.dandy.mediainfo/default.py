# -*- coding: utf-8 -*-
# Writer (c) 2017, dandy
# Rev. 1.0.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcaddon
import xbmcgui
import re
import sys, os
import simplejson as json

sys.path.append(os.path.dirname(__file__)+ '/../script.extendedinfo/resources/lib')
import TheMovieDB as tmdb

ID = "context.dandy.mediainfo"
ADDON = xbmcaddon.Addon(ID)

PATTERNS_FOR_EDIT = ADDON.getSetting('patterns_edit') if ADDON.getSetting('patterns_edit') else r"(.*)"

_title_ = ""
_year_ = ""
_movie_id_ = ""

def get_title():
    return xbmc.getInfoLabel("ListItem.Title") if xbmc.getInfoLabel("ListItem.Title") else xbmc.getInfoLabel("ListItem.Label")

def check_is_edit(title):
    isedit = False
    if ADDON.getSetting('is_edit') == "true":
        patterns = PATTERNS_FOR_EDIT.split(",") if PATTERNS_FOR_EDIT else []
        isedit = False
        for pattern in patterns:
            match = re.match(pattern, title)
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
            title = kbd.getText()
        else: 
            title = ""
    return title

def get_media_title():
    title = get_title()
    patterns = [r"[(].+?[)]", r"[[].+?[]]"]
    for pattern in patterns:
        title = re.sub(pattern, "", title).strip()
    title = title.split("/")[0].strip()
    title = edit_title(title) 
    return title

def get_media_meta_year():
    title = get_title()
    pattern = r"[([]([12][90]\d\d)[]), ]"
    match = re.search(pattern, title)
    return match.group(1) if match else ""

def get_date_by_tag(item):
    try:
        return item["release_date"].split("-")[0]
    except:
        return item["first_air_date"].split("-")[0]

def select_media(data):
    global _year_
    media = []
    for item in data:
        try:
            title = item["title"]
        except:
            title = None
        if title:
            media.append("%s [%s]" % (title, get_date_by_tag(item)))
#tmdb={u'total_results': 1, u'total_pages': 1, u'page': 1, u'results': [{u'poster_path': u'/jB5VQeYO2nr4h31RjXnnER9JoRN.jpg', u'title': u'\u0421\u0444\u0435\u0440\u0430', u'overview': u'\u0424\u0438\u043b\u044c\u043c \u0440\u0430\u0441\u0441\u043a\u0430\u0436\u0435\u0442 \u043e\u0431 \u0438\u043d\u0442\u0435\u0440\u043d\u0435\u0442-\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438 The Circle, \u043e\u0431\u044a\u0435\u0434\u0438\u043d\u044f\u044e\u0449\u0435\u0439 \u0432 \u0435\u0434\u0438\u043d\u0443\u044e \u0441\u0438\u0441\u0442\u0435\u043c\u0443 \u044d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u0443\u044e \u043f\u043e\u0447\u0442\u0443 \u0441\u0432\u043e\u0438\u0445 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439, \u0441\u0442\u0440\u0430\u043d\u0438\u0447\u043a\u0438 \u0432 \u0441\u043e\u0446\u0438\u0430\u043b\u044c\u043d\u044b\u0445 \u0441\u0435\u0442\u044f\u0445, \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044e \u043e \u0431\u0430\u043d\u043a\u043e\u0432\u0441\u043a\u0438\u0445 \u043a\u0430\u0440\u0442\u0430\u0445 \u0438 \u043f\u043e\u043a\u0443\u043f\u043a\u0430\u0445. \u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u043e\u043c \u044d\u0442\u043e\u0433\u043e \u043f\u0440\u043e\u0446\u0435\u0441\u0441\u0430 \u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u0441\u044f \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u0435 \u0447\u0435\u043b\u043e\u0432\u0435\u043a\u043e\u043c \u0443\u043d\u0438\u0432\u0435\u0440\u0441\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u043e\u043d\u043b\u0430\u0439\u043d-\u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u0430. \u041d\u043e \u043d\u0430 \u043f\u0440\u0430\u043a\u0442\u0438\u043a\u0435 \u043d\u0435 \u0432\u0441\u0435 \u0442\u0430\u043a \u0433\u043b\u0430\u0434\u043a\u043e: \u043f\u0440\u043e\u0435\u043a\u0442, \u043f\u043e\u0437\u0438\u0446\u0438\u043e\u043d\u0438\u0440\u0443\u0435\u043c\u044b\u0439 \u043a\u0430\u043a \u043d\u043e\u0432\u0430\u044f \u0441\u0442\u0443\u043f\u0435\u043d\u044c \u0432 \u0440\u0430\u0437\u0432\u0438\u0442\u0438\u0438 \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0439, \u043f\u0440\u0435\u0441\u043b\u0435\u0434\u0443\u0435\u0442 \u0438 \u0434\u0440\u0443\u0433\u0438\u0435, \u0431\u043e\u043b\u0435\u0435 \u0433\u0440\u044f\u0437\u043d\u044b\u0435 \u0446\u0435\u043b\u0438.', u'release_date': u'2017-04-27', u'popularity': 9.357582, u'original_title': u'The Circle', u'backdrop_path': u'/mYpuI61SFcFD9UCkJOLGVxZkIfz.jpg', u'vote_count': 3, u'video': False, u'adult': False, u'vote_average': 0.5, u'original_language': u'en', u'id': 339988, u'genre_ids': [18, 53, 878]}]}
    ret = 0
    if len(media) > 0:
        ret = xbmcgui.Dialog().select("Select media", media)
        if ret >= 0:
            _year_ = get_date_by_tag(data[ret])
            return str(data[ret]["id"])
        else:
            return None
    else:
        return ""

def get_media_category():
    if xbmc.getCondVisibility("Container.Content(tvshows)"):
        return "tv"
    else:
        return "multi"

def get_media_meta_movie_id():
    if _title_ == "":
        return ""
    global _year_
    params = {"query": "%s" % _title_,
              "language": "ru",
              "include_adult": True}
    if _year_ != "":
        params["year"] = int(_year_)
    response = tmdb.get_data(url="search/%s" % (get_media_category()),
                        params=params,
                        cache_days=1)
    if response and (not (response == "Empty")):
        if response["total_results"] > 0:
            if response["total_results"] == 1:
                _year_ = get_date_by_tag(response['results'][0])
                return str(response['results'][0]["id"])
            else:
                return select_media(response["results"])
        else:
            return ""
    else:
        return ""

def get_params():
    params = "info=extendedtvinfo" if xbmc.getCondVisibility("Container.Content(tvshows)") else "info=extendedinfo"
    if _movie_id_ == "":
        params = params + ",name=%s" % _title_
    if _year_ != "":
        params = params + ",year=%s" % _year_
    if xbmc.getInfoLabel("ListItem.DBID") and (xbmc.getInfoLabel("ListItem.DBID") != "-1"):
        params = params + ",dbid=%s" % xbmc.getInfoLabel("ListItem.DBID")
    if xbmc.getInfoLabel("ListItem.Property(id)"):
        params = params + ",id=%s" % xbmc.getInfoLabel("ListItem.Property(id)")
    elif _movie_id_ != "":
        params = params + ",id=%s" % _movie_id_
    return params

def check_params():
    check = True
    if _title_ == "":
        check = False
    if _movie_id_ == None:
        check = False
    return check

def main():
    global _title_, _year_, _movie_id_
    _title_ = get_media_title()
    _year_ = get_media_meta_year()
    _movie_id_ = get_media_meta_movie_id()
    if check_params():
        xbmc.executebuiltin("RunScript(script.extendedinfo,%s)" % get_params())

if __name__ == '__main__':
    main()
