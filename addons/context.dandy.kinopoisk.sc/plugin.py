import os
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
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

import resources.lib.hdgo as hdgo
import resources.lib.videoframe as videoframe
import resources.lib.hdbaza as hdbaza

from videohosts import iframe
from videohosts import videocdn
from videohosts import hdvb
from videohosts import collaps

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
        content = response["content"].decode("utf-8")
        try:
            div = common.parseDOM(content, "div", attrs={"id": "headerFilm"})[0]
            media_title_ = strip_(encode_('utf-8', common.parseDOM(div, "h1")[0]))
        except:
            pass
    return replace_(media_title_)


def get_media_image(kp_id):
    return "https://st.kp.yandex.net/images/film_big/" + kp_id + ".jpg"

def search_kp_id(media_title, mode):
    media = []
    media_titles = []

    response = common.fetchPage({"link": "http://www.kinopoisk.ru/index.php?first=no&what=&kp_query=" + urllib.parse.quote_plus(media_title)})
    if response["status"] == 200:
        try:
            content = response["content"].decode()
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
        show_message("Not found media")
        return None

def get_user_input_id():
    dialog = xbmcgui.Dialog()
    kp_id = None
    result = dialog.input('Input Kinopoisk ID', '', type = xbmcgui.INPUT_NUMERIC)
    if result:
        kp_id = result
    return kp_id

def get_user_input_title():
    dialog = xbmcgui.Dialog()
    title = None
    result = dialog.input('Input Title', '')
    if result:
        title = result
    return title

def get_user_input():
    variants = ["Search by ID", "Search by Title"]
    dialog = xbmcgui.Dialog()
    index_ = dialog.select("Select search type", variants)
    if (index_ == 0):
        return get_user_input_id()
    elif (index_ == 1):
        title = get_user_input_title()
        if title:
            return search_kp_id(title, None)
        else: 
            return None    

def get_kp_id(media_title, mode):
    if media_title:
        return search_kp_id(media_title, mode)
    else:
        return get_user_input()

def get_engine(data):
    if 'hdgo' in data:
        return 'hdgo'
    elif 'videoframe' in data:
        return 'videoframe'
    elif 'hdnow' in data:
        return 'hdnow'
    elif 'iframe' in data:
        return 'iframe'
    elif 'hdbaza' in data:
        return 'hdbaza'
    elif 'videocdn' in data:
        return 'videocdn'
    elif 'hdvb' in data:
        return 'hdvb'
    elif 'collaps' in data:
        return 'collaps'
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
    #if mode == "search":
    #    process(kp_id, media_title, image)
    #else:    
    film_title = " %s" % (orig_title)
    uri = sys.argv[0] + '?mode=process&kp_id=%s&media_title=%s&image=%s' % (kp_id, urllib.parse.quote_plus(media_title), urllib.parse.quote_plus(image))
    item = xbmcgui.ListItem(film_title)
    item.setArt({ 'thumb': image, 'icon' : image })
    item.setInfo(type='Video', infoLabels={'title': film_title, 'label': film_title, 'plot': film_title})
    xbmcplugin.addDirectoryItem(HANDLE, uri, item, True)
    xbmcplugin.setContent(HANDLE, 'movies')
    xbmcplugin.endOfDirectory(HANDLE, True)

def process(kp_id, media_title, image):
    if (not kp_id):
        kp_id, media_title, media_title, image = prepare("process", kp_id, media_title, media_title, image)
    if (not kp_id):
        return
    list_li = []
    list_li = search.process(kp_id)
    
    for li in list_li:
        engine = get_engine(li[1].getLabel())
        
        li[0] = li[0] + ("&media_title=%s&image=%s&engine=%s" % ((urllib.parse.quote_plus(encode_("utf-8", media_title))) if (media_title != "") else "", image, engine))
        li[1].setArt({ 'thumb': image, 'icon' : image })
        if ("*T*" in li[1].getLabel()):
            title = li[1].getLabel().replace("*T*", media_title)
            li[1].setLabel(title)
            li[0] = li[0] + ("&title=%s" % (urllib.parse.quote_plus(title)))
                
        li[1].setInfo(type='Video', infoLabels={'title': li[1].getLabel(), 'label': media_title, 'plot': media_title})
        xbmcplugin.addDirectoryItem(HANDLE, li[0], li[1], li[2])
    xbmcplugin.setContent(HANDLE, 'movies')
    xbmcplugin.endOfDirectory(HANDLE, True)

def show_hdgo(url, title):
    return hdgo.get_playlist(url)

def show_videoframe(url, title):
    return videoframe.get_playlist(url)

def show_iframe(url, title):
    return iframe.get_playlist(url)

def show_hdbaza(url, title):
    return hdbaza.get_playlist(url)

def show_videocdn(url, title):
    return videocdn.get_playlist(url)

def show_hdvb(url, title):
    return hdvb.get_playlist(url)

def show_collaps(url, title):
    return collaps.get_playlist(url)

def show(url, title, media_title, image, engine):
    manifest_links = {} 
    subtitles = None
    if (not media_title):
        media_title = title
    direct = 0
    if 'hdgo' in engine:
        manifest_links, subtitles, season, episode = show_hdgo(url, title)
    elif ('videoframe' in engine):
        manifest_links, subtitles, season, episode = show_videoframe(url, title)
    elif ('iframe' in engine):
        manifest_links, subtitles, season, episode = show_iframe(url, title)
    elif ('hdbaza' in engine):
        manifest_links, subtitles, season, episode = show_hdbaza(url, title)
    elif ('videocdn' in engine):
        manifest_links, subtitles, season, episode = show_videocdn(url, title)
    elif ('hdvb' in engine):
        manifest_links, subtitles, season, episode = show_hdvb(url, title)
    elif ('collaps' in engine):
        manifest_links, subtitles, season, episode = show_collaps(url, title)
        direct = 1

    if manifest_links:
        list = sorted(iter(manifest_links.items()), key=itemgetter(0))
        if season:
            title += " - s%se%s" % (season.zfill(2), episode.zfill(2))
        for quality, link in list:
            film_title = "[COLOR=lightgreen][%s][/COLOR] %s" % (str(quality), title)
            try:
                uri = sys.argv[0] + '?mode=play&url=%s&title=%s&media_title=%s&direct=%d' % (urllib.parse.quote_plus(link), urllib.parse.quote_plus(title), urllib.parse.quote_plus(media_title), direct)
            except:    
                uri = sys.argv[0] + '?mode=play&url=%s&title=%s&media_title=%s&direct=%d' % (link, title, media_title, direct)            
            item = xbmcgui.ListItem(film_title)
            item.setArt({ 'thumb': image, 'icon' : image })
            item.setInfo(type='Video', infoLabels={'title': film_title, 'label': film_title, 'plot': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
            item.setProperty('IsPlayable', 'true')
            if subtitles: 
                #urls = re.compile('http:\/\/.*?\.srt').findall(subtitles)
                item.setSubtitles([subtitles])
            xbmcplugin.addDirectoryItem(HANDLE, uri, item, False)
        xbmcplugin.setContent(HANDLE, 'movies')
        xbmcplugin.endOfDirectory(HANDLE, True)


def play(url, direct):
    if (direct != 1) and ("m3u8" in url):
        url = ("http:" if (not (("http://" in url) or ("https://" in url))) else "") + url
        response = common.fetchPage({"link": url})
        if (not (("http://" in response["content"].decode("utf-8")) or ("https://" in response["content"].decode("utf-8")))):
            content = response["content"].decode("utf-8").split("\n")
            name = os.path.join(PATH, 'resources/playlists/') + "temp.m3u8"
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
        return param.encode(code)
    except:
        return param

def strip_(string):
    return common.stripTags(string)

def replace_(string):
    return string.replace("&ndash;", "/").replace("&nbsp;", " ")

def show_message(msg):
    xbmc.executebuiltin("XBMC.Notification(%s, %s, %s)" % ("ERROR", msg, str(5 * 1000)))

def main():
    PARAMS = common.getParameters(sys.argv[2])
    kp_id = PARAMS['kp_id'] if ('kp_id' in PARAMS) else None
    mode = PARAMS['mode'] if 'mode' in PARAMS else None
    url = urllib.parse.unquote_plus(PARAMS['url']) if 'url' in PARAMS else None
    title = urllib.parse.unquote_plus(PARAMS['title']) if 'title' in PARAMS else None
    orig_title = urllib.parse.unquote_plus(PARAMS['orig_title']) if 'orig_title' in PARAMS else None    
    media_title = urllib.parse.unquote_plus(PARAMS['media_title']) if 'media_title' in PARAMS else None
    if orig_title == None:
        orig_title = media_title
    image = urllib.parse.unquote_plus(PARAMS['image']) if 'image' in PARAMS else None
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