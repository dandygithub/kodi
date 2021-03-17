# -*- coding: utf-8 -*-
# Writer (c) 2018-2021, dandy
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import simplejson as json
import time

ID = "script.dandy.strm.marker"
ADDON = xbmcaddon.Addon(ID)
PATH = ADDON.getAddonInfo('path')

IS_MOVIES = ADDON.getSetting('movies') if ADDON.getSetting('movies') else "false"
IS_TVSHOWS = ADDON.getSetting('tvshows') if ADDON.getSetting('tvshows') else "false"

ACTION = ADDON.getSetting('action') if ADDON.getSetting('action') else None
TYPE = ADDON.getSetting('type') if ADDON.getSetting('type') else None
TEXT = ADDON.getSetting('text') if ADDON.getSetting('text') else None

def show_message(msg):
    xbmc.executebuiltin("XBMC.Notification(%s, %s, %s)" % ("MESSAGE", msg, str(5 * 1000)))

REQUEST = {'jsonrpc': '2.0',
           'method': '{0}',
           'params': '{1}',
           'id': 1
           }

def jsonrpc(method, params):
    request = REQUEST
    request['method'] = method
    request['params'] = params
    response = xbmc.executeJSONRPC(json.dumps(request))
    j = json.loads(response)
    return j.get('result')

def clear_movie(movie):
    fn = movie.get("file")
    result = (".strm" in fn)
    if result == True:
        movie = clear_movie_title(movie)
        title = movie.get("title")
        reply = jsonrpc("VideoLibrary.SetMovieDetails", {'movieid': movie.get("movieid"), "title": title})
    return result

def clear_movie_title(movie):
    title = movie.get("title")
    title = title.replace(TEXT, "").strip()
    movie["title"] = title
    return movie

def modify_movie(movie):
    fn = movie.get("file")
    result = (".strm" in fn)
    if result == True:
        if TYPE == '0':
            movie = clear_movie_title(movie)
            title = movie.get("title")
            title = TEXT + ' ' + title
        elif TYPE == '1':
            movie = clear_movie_title(movie)
            title = movie.get("title")
            title = title + ' ' + TEXT
        reply = jsonrpc("VideoLibrary.SetMovieDetails", {'movieid': movie.get("movieid"), "title": title})
    return result

def check_tvshow(tvshow):
    result = False
    reply = jsonrpc("VideoLibrary.GetEpisodes", {'tvshowid': tvshow.get("tvshowid"), 'properties': ['title', 'file']})
    if reply:
        episodes = reply.get("episodes")
        if (len(episodes) > 0):
            episode = episodes[0]
            fn = episode.get("file")
            result = (".strm" in fn)
    return result

def clear_tvshow(tvshow):
    result = check_tvshow(tvshow)
    if result == True:
        tvshow = clear_tvshow_title(tvshow)
        title = tvshow.get("title")
        reply = jsonrpc("VideoLibrary.SetTVShowDetails", {'tvshowid': tvshow.get("tvshowid"), "title": title})
    return result

def clear_tvshow_title(tvshow):
    title = tvshow.get("title")
    title = title.replace(TEXT, "").strip()
    tvshow["title"] = title
    return tvshow

def modify_tvshow(tvshow):
    result = check_tvshow(tvshow)
    if result == True:
        if TYPE == '0':
            tvshow = clear_tvshow_title(tvshow)
            title = tvshow.get("title")
            title = TEXT + ' ' + title
        elif TYPE == '1':
            tvshow = clear_tvshow_title(tvshow)
            title = tvshow.get("title")
            title = title + ' ' + TEXT
        reply = jsonrpc("VideoLibrary.SetTVShowDetails", {'tvshowid': tvshow.get("tvshowid"), "title": title})
    return result

def get_movies():
    result = jsonrpc("VideoLibrary.GetMovies", {'properties': ['title', 'genre', 'year', 'file']})
    return result.get("movies"), result.get("limits")

def mark_movies():
    movies, limits = get_movies()
    total = limits.get("total")
    progress = xbmcgui.DialogProgress()
    progress.create("Mark (Movies)", "Please wait. Marking...")
    modify = 0
    for i, movie in enumerate(movies):
        if (progress.iscanceled()):
            break

        if modify_movie(movie):
            modify += 1

        result_string = "{0}: {1}".format("Mark results", modify)
        progress.update(int((100 * i )/ total), movie.get("title"))

#        time.sleep(0.1)
    progress.close()

def get_tvshows():
    result = jsonrpc("VideoLibrary.GetTVShows", {'properties': ['title', 'genre', 'year', 'file']})
    return result.get("tvshows"), result.get("limits")

def mark_tvshows():
    tvshows, limits = get_tvshows()
    total = limits.get("total")
    progress = xbmcgui.DialogProgress()
    progress.create("Mark (TVShows)", "Please wait. Marking...")
    modify = 0
    for i, tvshow in enumerate(tvshows):
        if (progress.iscanceled()):
            break

        if modify_tvshow(tvshow):
            modify += 1

        result_string = "{0}: {1}".format("Mark results", modify)
        progress.update(100 * i / total, line2=tvshow.get("title"), line3=result_string)

#        time.sleep(0.1)
    progress.close()

def mark():
    if (IS_MOVIES == "true"):
        mark_movies()
    if (IS_TVSHOWS == "true"):
        mark_tvshows()

def clear_movies():
    movies, limits = get_movies()
    total = limits.get("total")
    progress = xbmcgui.DialogProgress()
    progress.create("Clear (Movies)", "Please wait. Clearing...")
    modify = 0
    for i, movie in enumerate(movies):
        if (progress.iscanceled()):
            break

        if clear_movie(movie):
            modify += 1

        result_string = "{0}: {1}".format("Clear results", modify)
        progress.update(100 * i / total, line2=movie.get("title"), line3=result_string)

#        time.sleep(0.1)
    progress.close()

def clear_tvshows():
    tvshows, limits = get_tvshows()
    total = limits.get("total")
    progress = xbmcgui.DialogProgress()
    progress.create("Clear (TVShows)", "Please wait. Clearing...")
    modify = 0
    for i, tvshow in enumerate(tvshows):
        if (progress.iscanceled()):
            break

        if clear_tvshow(tvshow):
            modify += 1

        result_string = "{0}: {1}".format("Clear results", modify)
        progress.update(100 * i / total, line2=tvshow.get("title"), line3=result_string)

#        time.sleep(0.1)
    progress.close()

def clear():
    if (IS_MOVIES == "true"):
        clear_movies()
    if (IS_TVSHOWS == "true"):
        clear_tvshows()

def action():
    if (ACTION == '0'):
        mark()
    else:
        clear()

def main():
    action()

if __name__ == '__main__':
    main()
