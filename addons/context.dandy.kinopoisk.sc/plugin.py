import os
import urllib, urllib2
import re
import socket
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
from operator import itemgetter
import XbmcHelpers
common = XbmcHelpers

import resources.lib.search as search

import resources.lib.moonwalk as moonwalk
import resources.lib.hdgo as hdgo
import resources.lib.kodik as kodik
import resources.lib.videoframe as videoframe

socket.setdefaulttimeout(120)

HANDLE = int(sys.argv[1])
ID = 'context.dandy.kinopoisk.sc'
ADDON = xbmcaddon.Addon(ID)
PATH = ADDON.getAddonInfo('path')

EXT_SEARCH = ADDON.getSetting('ext_search') if ADDON.getSetting('ext_search') else "false"

PARAMS = None
MODE = None

def get_media_title(kp_id, media_title):
    if not kp_id:
        return media_title

    if media_title:
        media_title_ = media_title
    else:
        media_title_ = "<" + kp_id + ">"

    response = common.fetchPage({"link": "https://www.kinopoisk.ru/film/" + kp_id + "/"})

    if response["status"] == 200:
        content = response["content"]
        try:
            div = common.parseDOM(content, "div", attrs={"id": "headerFilm"})[0]
            media_title_ = strip_(encode_('utf-8', decode_('cp1251', common.parseDOM(div, "h1")[0])))
        except:
            pass
    return media_title_


def get_media_image(kp_id):
    return "https://st.kp.yandex.net/images/film_big/" + kp_id + ".jpg"

def search_kp_id(media_title, mode):
    media = []
    media_titles = []

    response = common.fetchPage({"link": "http://www.kinopoisk.ru/index.php?first=no&what=&kp_query=" + urllib.quote_plus(media_title)})

    if response["status"] == 200:
        content = response["content"]

        try:
            div = common.parseDOM(content, "div", attrs={"class": "search_results"})[0]
            info = common.parseDOM(div, "div", attrs={"class": "info"})[0]
            title = encode_('utf-8', decode_('cp1251', common.parseDOM(info, "a")[0]))
            media.append(common.parseDOM(info, "a", ret="data-id")[0])            
            media_titles.append(replace_(title + " (" + common.parseDOM(info, "span")[0] + ")"))
            if (EXT_SEARCH == "true") and (mode != "search"):
                divmain = common.parseDOM(content, "div", attrs={"class": "search_results search_results_last"})[0]
                divs = common.parseDOM(divmain, "div", attrs={"class": "element"})
                for div in divs:
                    info = common.parseDOM(div, "div", attrs={"class": "info"})[0]
                    title = encode_('utf-8', decode_('cp1251', common.parseDOM(info, "a")[0]))
                    if media_title.decode('utf-8').upper() == title.decode('utf-8').upper(): 
                        media.append(common.parseDOM(info, "a", ret="data-id")[0])
                        media_titles.append(replace_(title + " (" + common.parseDOM(info, "span")[0] + ")"))
        except:
            pass

    ret = 0
    if len(media) > 0:
        if len(media) > 1:
            ret = xbmcgui.Dialog().select("Select media", media_titles)
        if ret >= 0:
            return media[ret]
        else:
            return None
    else:
        return None

def get_user_input():
    dialog = xbmcgui.Dialog()
    kp_id = None
    result = dialog.input('Input Kinopoisk ID', '', type = xbmcgui.INPUT_NUMERIC)
    if result:
        kp_id = result
    return kp_id

def get_kp_id(media_title, mode):
    if media_title:
        return search_kp_id(media_title, mode)
    else:
        return get_user_input()

def get_engine(data):
    if 'moonwalk' in data:
        return 'moonwalk'
    elif 'hdgo' in data:
        return 'hdgo'
    elif 'kodik' in data:
        return 'kodik'
    elif 'videoframe' in data:
        return 'videoframe'
    elif 'hdnow' in data:
        return 'hdnow'
    else:
        return 'none'

def prepare(mode, kp_id, orig_title, media_title, image):
    search_kp_id = False 
    if (not kp_id):
        kp_id = get_kp_id(media_title, mode)
        search_kp_id = True 
    if (not kp_id):
        return None, "", "", ""

    media_title = get_media_title(kp_id, media_title)
    if orig_title == None:
        orig_title = media_title
    image = get_media_image(kp_id)

    return kp_id, orig_title, media_title, image

def main_(mode, kp_id, orig_title, media_title, image):
    kp_id, orig_title, media_title, image = prepare(mode, kp_id, orig_title, media_title, image)
    if (not kp_id):
        return
    if mode == "search":
        process(kp_id, media_title, image)
    else:    
        film_title = " %s" % (orig_title)
        uri = sys.argv[0] + '?mode=process&kp_id=%s&media_title=%s&image=%s' % (kp_id, urllib.quote_plus(media_title), urllib.quote_plus(image))
        item = xbmcgui.ListItem(film_title, iconImage=image, thumbnailImage=image)
        item.setInfo(type='Video', infoLabels={'title': film_title, 'label': film_title, 'plot': film_title})
        xbmcplugin.addDirectoryItem(HANDLE, uri, item, True)
        xbmcplugin.setContent(HANDLE, 'movies')
        xbmcplugin.endOfDirectory(HANDLE, True)


def process(kp_id, media_title, image):
    list_li = []
    list_li = search.process(kp_id)
    for li in list_li:
        engine = get_engine(li[1].getLabel())
        li[0] = li[0] + ("&media_title=%s&image=%s&engine=%s" % ((urllib.quote_plus(media_title)) if (media_title != "") else "", image, engine))
        li[1].setIconImage(image)
        li[1].setThumbnailImage(image)
        if ("*T*" in li[1].getLabel()):
            title = li[1].getLabel().replace("*T*", media_title)
            li[1].setLabel(title)
            li[0] = li[0] + ("&title=%s" % (urllib.quote_plus(title)))
        li[1].setInfo(type='Video', infoLabels={'title': media_title, 'label': media_title, 'plot': media_title})
        xbmcplugin.addDirectoryItem(HANDLE, li[0], li[1], li[2])
    xbmcplugin.setContent(HANDLE, 'movies')
    xbmcplugin.endOfDirectory(HANDLE, True)

def show_moonwalk(url, title):
    return moonwalk.get_playlist(url)

def show_hdgo(url, title):
    return hdgo.get_playlist(url)

def show_kodik(url, title):
    return kodik.get_playlist(url)

def show_videoframe(url, title):
    return videoframe.get_playlist(url)

def show(url, title, media_title, image, engine):
    manifest_links = {} 
    subtitles = None
    if (not media_title):
        media_title = title
    direct = 0
    if ('moonwalk' in engine) or ('hdnow' in engine):
        manifest_links, subtitles, season, episode = show_moonwalk(url, title)
        direct = 1
    elif 'hdgo' in engine:
        manifest_links, subtitles, season, episode = show_hdgo(url, title)
    elif 'kodik' in engine:
        manifest_links, subtitles, season, episode, direct = show_kodik(url, title)
    elif 'videoframe' in engine:
        manifest_links, subtitles, season, episode = show_videoframe(url, title)

    if manifest_links:
        list = sorted(manifest_links.iteritems(), key=itemgetter(0))
        if season:
            title += " - s%se%s" % (season.zfill(2), episode.zfill(2)) 
        for quality, link in list:
            film_title = "[COLOR=lightgreen][%s][/COLOR] %s" % (str(quality), title)
            uri = sys.argv[0] + '?mode=play&url=%s&title=%s&media_title=%s&direct=%d' % (urllib.quote_plus(link), urllib.quote_plus(title), urllib.quote_plus(media_title), direct)
            item = xbmcgui.ListItem(film_title, iconImage=image, thumbnailImage=image)
            item.setInfo(type='Video', infoLabels={'title': film_title, 'label': film_title, 'plot': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
            item.setProperty('IsPlayable', 'true')
            if subtitles: 
                urls = re.compile('http:\/\/.*?\.srt').findall(subtitles)
                item.setSubtitles(urls)
            xbmcplugin.addDirectoryItem(HANDLE, uri, item, False)
        xbmcplugin.setContent(HANDLE, 'movies')
        xbmcplugin.endOfDirectory(HANDLE, True)


def play(url, direct):
    if (direct != 1) and ("m3u8" in url):
        url = ("http:" if (not (("http://" in url) or ("https://" in url))) else "") + url
        response = common.fetchPage({"link": url})
        if (not (("http://" in response["content"]) or ("https://" in response["content"]))):
            content = response["content"].split("\n")
            name = os.path.join(PATH.decode("utf-8"), 'resources/playlists/') + "temp.m3u8"
            block = url.split("mp4")[0]
            f = open(name, "w+")
            for line in content:
               if "mp4" in line:
                   line = block + "mp4" + line.split("mp4")[-1]
               f.write(line + "\n")
            f.close()
            item = xbmcgui.ListItem(path=name)
        else:
            item = xbmcgui.ListItem(path=url) 
    else:
        item = xbmcgui.ListItem(path=url) 
    xbmcplugin.setResolvedUrl(HANDLE, True, item)

def decode_(code, param):
    try:
        return param.decode(code)
    except:
        return param

def encode_(code, param):
    try:
        return unicode(param).encode(code)
    except:
        return param

def strip_(string):
    return common.stripTags(string)

def replace_(string):
    return string.replace("&ndash;", "/")

def main():
    PARAMS = common.getParameters(sys.argv[2])
    kp_id = PARAMS['kp_id'] if ('kp_id' in PARAMS) else None
    mode = PARAMS['mode'] if 'mode' in PARAMS else None
    url = urllib.unquote_plus(PARAMS['url']) if 'url' in PARAMS else None
    title = urllib.unquote_plus(PARAMS['title']) if 'title' in PARAMS else None
    orig_title = urllib.unquote_plus(PARAMS['orig_title']) if 'orig_title' in PARAMS else None    
    media_title = urllib.unquote_plus(PARAMS['media_title']) if 'media_title' in PARAMS else None
    if orig_title == None:
        orig_title = media_title
    image = urllib.unquote_plus(PARAMS['image']) if 'image' in PARAMS else None
    direct = int(PARAMS['direct']) if 'direct' in PARAMS else None
    engine = PARAMS['engine'] if 'engine' in PARAMS else None

    if (not mode) or (mode == "context") or (mode == "search"):
        main_(mode, kp_id, orig_title, media_title, image)
    elif mode == "process":
        process(kp_id, media_title, image)    
    elif mode == "show":
        show(url, title, media_title, image, engine)
    elif mode == "play":
        play(url, direct)

if __name__ == '__main__':
    main()