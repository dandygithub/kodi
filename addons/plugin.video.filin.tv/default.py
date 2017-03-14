#!/usr/bin/python
# Writer (c) 2012-2017, MrStealth, dandy
# Rev. 2.2.0
# -*- coding: utf-8 -*-

import os
import urllib, re, sys
import xbmc, xbmcplugin,xbmcgui,xbmcaddon
import HTMLParser
import XbmcHelpers
import json

from urllib2 import Request, urlopen, URLError
common = XbmcHelpers

BASE_URL = 'http://www.filin.tv'
pluginhandle = int(sys.argv[1])

ID = 'plugin.video.filin.tv'
Addon = xbmcaddon.Addon(id=ID)
language      = Addon.getLocalizedString
addon_icon    = Addon.getAddonInfo('icon')
addon_path    = Addon.getAddonInfo('path')

import Translit as translit
translit = translit.Translit()

# UnifiedSearch
use_unified = True
try:
    sys.path.append(os.path.dirname(__file__)+ '/../plugin.video.unified.search')
    from unified_search import UnifiedSearch
except: 
    use_unified = False
    pass

VIEW_MODES = {
    "List" : '50',
    "Big List" : '51',
    "Media Info" : '52',
    "Media Info 2" : '54',
    "Fanart" : '57',
    "Fanart 2" : '59'
}

# *** Python helpers ***
def strip_html(text):
  def fixup(m):
    text = m.group(0)
    if text[:1] == "<":
      if text[1:3] == 'br':
        return '\n'
      else:
        return ""
    if text[:2] == "&#":
      try:
        if text[:3] == "&#x":
          return chr(int(text[3:-1], 16))
        else:
          return chr(int(text[2:-1]))
      except ValueError:
        pass
    elif text[:1] == "&":
      import htmlentitydefs
      if text[1:-1] == "mdash":
        entity = " - "
      elif text[1:-1] == "ndash":
        entity = "-"
      elif text[1:-1] == "hellip":
        entity = "-"
      else:
        entity = htmlentitydefs.entitydefs.get(text[1:-1])
      if entity:
        if entity[:2] == "&#":
          try:
            return chr(int(entity[2:-1]))
          except ValueError:
            pass
        else:
          return entity
    return text
  ret =  re.sub("(?s)<[^>]*>|&#?\w+;", fixup, text)
  return re.sub("\n+", '\n' , ret)

def remove_extra_spaces(data):  # Remove more than one consecutive white space
    p = re.compile(r'\s+')
    return p.sub(' ', data)

def unescape(entity, encoding):
  if encoding == 'utf-8':
    return HTMLParser.HTMLParser().unescape(entity).encode(encoding)
  elif encoding == 'cp1251':
    return entity.decode(encoding).encode('utf-8')

def localize(string):
    return unescape(string, 'utf-8')

def colorize(string, color):
    text = "[COLOR " + color + "]" + string + "[/COLOR]"
    return text

def get_url(string):
  return re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+.xml', string)[0]


# *** XBMC helpers ***
def xbmcItem(url, title, mode, *args):
    item = xbmcgui.ListItem(title)
    uri = sys.argv[0] + '?mode='+ mode + '&url=' + url
    xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)


def get_params():
    param=[]
    paramstring = sys.argv[2]

    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')

        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')

        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param


# *** Addon helpers ***
def beatify_title(title):
  title = unescape(title, 'cp1251').replace(language(5000).encode('utf-8'),"")
  return title.replace(language(5001).encode('utf-8'),"")


def getDescription(block):
    html = block[block.find('</h2>'):len(block)]
    return unescape(strip_html(remove_extra_spaces(html)), 'cp1251')

    #return unescape(remove_extra_spaces(remove_html_tags(html)), 'cp1251')


def getThumbnail(block):
    thumbnail = common.parseDOM(block, "img", ret = "src")[0]
    if thumbnail[0] == '/': thumbnail = BASE_URL+thumbnail
    return thumbnail


def getTitle(block):
    title = common.parseDOM(block, "a")
    return title[len(title)-1]


def calculateRating(x):
    rating = (int(x)*100)/100
    xbmc_rating = (rating*10)/100
    return xbmc_rating

# *** UI functions ***

def getUserInput():
    kbd = xbmc.Keyboard()
    kbd.setDefault('')
    kbd.setHeading(language(2002))
    kbd.doModal()
    keyword = None

    if kbd.isConfirmed():
        if Addon.getSetting('translit') == 'true':
            keyword = translit.rus(kbd.getText())
        else:
            keyword = kbd.getText()

    return keyword

def USTranslit(keyword, external, transpar):
    if external == 'usearch':
        return urllib.unquote_plus(keyword)
    else:
        return translit.rus(keyword) if ((transpar == None) or (transpar == "true")) else keyword

def search(keyword, external, transpar = None):

    if (external == 'unified') and (use_unified == False):
        return

    keyword = USTranslit(keyword, external, transpar) if (external != None) else getUserInput()
    if not keyword:
        return

    # Advanced search: titles only
#    values = {
#      'beforeafter' : 'after',
#      'catlist[]' : '0',
#      'do' : 'search',
#      'full_search' : '1',
#      'replyless' : '0',
#      'replylimit' : '0',
#      'resorder' : 'desc',
#      'result_from' : '1',
#      'result_num' : '30',
#      'search_start' : '1',
#      'searchdate' : '0',
#      'searchuser' : '',
#      'showposts' : '0',
#      'sortby' : 'date',
#      'subaction' : 'search',
#      'titleonly' : '3'
#   }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "Host": "filin.tv",
        "Origin": "http://filin.tv",
        "Referer": "http://filin.tv/",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    }

    values = {
        'do' : 'search',
        'subaction' : 'search',
    }

    try:
        values['story'] = keyword.encode('cp1251')
    except UnicodeDecodeError:
        values['story'] = keyword

    data = urllib.urlencode(values)
    req = Request(BASE_URL+'/', data, headers)

    try:
        response = urlopen(req)
    except URLError, e:
        if hasattr(e, 'reason'):
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
        elif hasattr(e, 'code'):
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
    else:
        unified_search_results = []

        response = response.read()
        content = common.parseDOM(response, "div", attrs = { "id":"dle-content" })
        blocks = common.parseDOM(content, "div", attrs = { "class":"block" })

        #if (not unified):
        #    result = common.parseDOM(content, "span", attrs = { "class":"sresult" })[0]
        #    item = xbmcgui.ListItem(colorize(unescape(result, 'cp1251'), 'FF00FFF0'))
        #    item.setProperty('IsPlayable', 'false')
        #    xbmcplugin.addDirectoryItem(pluginhandle, '', item, False)

        mainf = common.parseDOM(content, "div", attrs = { "class":"mainf" })
        titles = common.parseDOM(mainf, "a")
        links = common.parseDOM(mainf, "a", ret = "href")

        lines = 0 
        for i in range(0, len(links)):
            title = beatify_title(titles[i])
            if keyword.decode('utf-8').upper() in title.decode('utf-8').upper(): 
                lines += 1

                uri = sys.argv[0] + '?mode=SHOW&url=' + links[i] + "&thumbnail="
 
                if (external == 'unified'):
                    unified_search_results.append({'title': title, 'url': links[i], 'image': addon_icon, 'plugin': ID})
                else:
                    item = xbmcgui.ListItem(title, iconImage=addon_icon, thumbnailImage=addon_icon)
      
                    # TODO: move to "addFavorite" function
                    script = "special://home/addons/plugin.video.filin.tv/contextmenuactions.py"
                    params = "add|%s"%links[i] + "|%s"%title
                    runner = "XBMC.RunScript(" + str(script)+ ", " + params + ")"
                    item.addContextMenuItems([(localize(language(3001)), runner)])
  
                    xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)

        if (lines == 0) and (external == None):
            item = xbmcgui.ListItem(colorize(language(2004), 'FFFF4000'))
            item.setProperty('IsPlayable', 'false')
            xbmcplugin.addDirectoryItem(pluginhandle, '', item, False)

        if (external == 'unified'):
            UnifiedSearch().collect(unified_search_results)
        else: 
            xbmcplugin.endOfDirectory(pluginhandle, True)


def getCategories(url):
    result = common.fetchPage({"link": url})

    if result["status"] == 200:
        content = common.parseDOM(result["content"], "div", attrs = { "class":"mcont" })
        categories = common.parseDOM(content, "a", ret="href")
        descriptions = common.parseDOM(content, "a")

        for i in range(0, len(categories)):
            uri = sys.argv[0] + '?url=' + BASE_URL + categories[i]
            title = unescape(descriptions[i], 'cp1251')

            item = xbmcgui.ListItem(title)
            xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)

    xbmcplugin.endOfDirectory(pluginhandle, True)

def getCategoryItems(url, categorie, page):
    print "*** getCategoryItems"
    path = url + "?onlyjanr=" + categorie
    page = int(page)

    response = common.fetchPage({"link": path})
    content = response['content']

    if response["status"] == 200:
        links = common.parseDOM(content, "a", ret="href")
        titles = common.parseDOM(content, "a")

        if page == 1:
            min=0
            max = {True: page*20, False: len(links)}[len(links) > (page*20)]
        else:
            min=(page-1)*20
            max= {True: page*20, False: len(links)}[len(links) > (page*20)]

        for i in range(min, max):
          uri = sys.argv[0] + '?mode=SHOW&url=' + links[i] + "&thumbnail="

          if titles[i] == '': titles[i] = "[Unknown]" #TODO: investigate title issue
          item = xbmcgui.ListItem(titles[i])

          # TODO: move to "addFavorite" function
          script = "special://home/addons/plugin.video.filin.tv/contextmenuactions.py"
          params = "add|%s"%links[i] + "|%s"%titles[i]
          runner = "XBMC.RunScript(" + str(script)+ ", " + params + ")"


          item.addContextMenuItems([(localize(language(3001)), runner)])
          xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)

        if max >= 20 and max < len(links):
            uri = sys.argv[0] + '?mode=CNEXT&url=' + url + '&page=' + str(page+1) + '&categorie=' + categorie
            item = xbmcgui.ListItem(localize(language(3000)))
            xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)

        xbmcplugin.endOfDirectory(pluginhandle, True)

def listGenres():
    genres = [
                 'http://www.filin.tv/otechestvennue/',
                 'http://www.filin.tv/detectiv/',
                 'http://www.filin.tv/romance/',
                 'http://www.filin.tv/action/',
                 'http://www.filin.tv/fantastika/',
                 'http://www.filin.tv/kriminal/',
                 'http://www.filin.tv/comedi/',
                 'http://www.filin.tv/teleshou/',
                 'http://www.filin.tv/multfilms/',
                 'http://www.filin.tv/adventure/',
                 'http://www.filin.tv/fantasy/',
                 'http://www.filin.tv/horror/',
                 'http://www.filin.tv/drama/',
                 'http://www.filin.tv/history/',
                 'http://www.filin.tv/triller/',
                 'http://www.filin.tv/mystery/',
                 'http://www.filin.tv/sport/',
                 'http://www.filin.tv/musical/',
                 'http://www.filin.tv/dokumentalnii/',
                 'http://www.filin.tv/war/'
    ]


    for i in range(0, len(genres)):
        uri = sys.argv[0] + '?&url=' + genres[i] + '/'
        item = xbmcgui.ListItem(localize(language(1000+i)))
        xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)

    xbmcplugin.endOfDirectory(pluginhandle, True)


def listFavorites():
    string = Addon.getSetting('favorites')

    if len(string) == 0:
        item = xbmcgui.ListItem(language(3002))
        xbmcplugin.addDirectoryItem(pluginhandle, '', item, False)
    else:
        favorites = json.loads(string.replace('\x00', ''))
        for key in favorites:
            item = xbmcgui.ListItem(favorites[key])

            # TODO: show thumbnail (item = xbmcgui.ListItem(key, thumbnailImage=thumbnail))
            uri = sys.argv[0] + '?mode=SHOW&url=' + key + '&thumbnail='
            item.setInfo( type='Video', infoLabels={'title': favorites[key]})

            # TODO: move to "addFavorite" function
            script = "special://home/addons/plugin.video.filin.tv/contextmenuactions.py"
            params = "remove|%s" % key + "|%s" % favorites[key]
            runner = "XBMC.RunScript(" + str(script)+ ", " + params + ")"
            item.addContextMenuItems([(localize(language(3004)), runner)])
            xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)

        item = xbmcgui.ListItem("[COLOR=FFFF4000]%s[/COLOR]" % language(3006))
        uri = sys.argv[0] + '?mode=RESET'
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)

    xbmcplugin.endOfDirectory(pluginhandle, True)

def resetFavorites():
    dialog = xbmcgui.Dialog()
    answer = dialog.yesno(language(3006), language(3007))
    if answer == 1:
      Addon.setSetting('favorites', '')

# Get latest income from index page
def getRecentItems(url):

    if url==BASE_URL:
        xbmcItem('', colorize(localize('['+language(2002)+']'), "FF00FF00"), 'SEARCH')
        xbmcItem('', colorize(localize(language(2003)), "FF00FFF0"), 'FAVORITES')
        xbmcItem('', colorize(localize(language(2000)), "FF00FFF0"), 'CATEGORIES')
#        xbmcItem('', colorize(localize(language(2001)), "FF00FFF0"), 'GENRES')

    getItems(url)


def getItems(url):
    print "*** getItems"

    response = common.fetchPage({"link": url})

    if response["status"] == 200:
        content = common.parseDOM(response["content"], "div", attrs = { "id":"dle-content" })
        blocknews = common.parseDOM(content, "div", attrs = { "class":"blocknews" })

        mainf = common.parseDOM(blocknews, "div", attrs = { "class":"mainf" })

        titles = common.parseDOM(mainf, "a")
        links = common.parseDOM(mainf, "a", ret="href")

        blocktext = common.parseDOM(content, "div", attrs = { "class":"block_text" })

        images = common.parseDOM(blocktext, "img", ret = "src")
        descriptions = common.parseDOM(blocktext, "td", attrs = { "style":"padding-left:10px;" })
        ratings = common.parseDOM(blocktext, "li", attrs={"class": "current-rating"})

        genres = []
        for i, g in enumerate(common.parseDOM(blocknews, "div", attrs = { "class":"categ" })):
            genres.append(" ".join(str(g) for g in common.parseDOM(g, "a")))

        for i, title in enumerate(titles):
            if images[i][0] == '/': images[i] = BASE_URL+images[i]
            title = beatify_title(title)
            genre = unescape(str(genres[i]), 'cp1251')

            description = unescape(descriptions[i].split('<br/>')[-1], 'cp1251')
            description = common.stripTags(description.split('</strong>')[-1])

            uri = sys.argv[0] + '?mode=SHOW&url=' + links[i] + '&thumbnail=' + images[i]
            item = xbmcgui.ListItem(title, iconImage = addon_icon, thumbnailImage=images[i])
            infoLabels={'title': title, 'genre' : genre, 'plot': description}

            if calculateRating(ratings[i]) > 0:
                infoLabels['rating'] = calculateRating(ratings[i])

            # print "Rating: %s - %d" % (ratings[i], calculateRating(ratings[i]))

            item.setInfo( type='Video', infoLabels=infoLabels)
            item.setProperty( "isFolder", 'True')

            # TODO: move to "addFavorite" function
            script = "special://home/addons/plugin.video.filin.tv/contextmenuactions.py"
            params = "add|%s"%links[i] + "|%s"%title
            runner = "XBMC.RunScript(" + str(script)+ ", " + params + ")"

            item.addContextMenuItems([(localize(language(3001)), runner)])
            xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)

    next = url + '/page/2' if url.find("page") == -1 else url[:-1] + str(int(url[-1])+1)

    xbmcItem(next, localize(language(3000)), 'RNEXT')

    try:
        mode = VIEW_MODES[Addon.getSetting('seasonsViewMode')]
        xbmc.executebuiltin("Container.SetViewMode(" + mode + ")")
    except Exception, e:
        print "*** Exception"
        print e
        xbmc.executebuiltin('Container.SetViewMode(50)')

    xbmcplugin.endOfDirectory(pluginhandle, True)

def selectQuality(url, index, title):
    url_ = url
    index_ = index
    if (url_.find('_[') > -1):
        qualities = url_[url_.find('_[')+2:url_.find('].mp4')]
        qlist = qualities.split(',')
        if (index_ == None): 
            if bestquality == "true":
                index_ = 0
            else: 
                qualities = url[url.find('_[')+2:url.find('].mp4')]
                qlist = qualities.split(',')
                if (qlist.count > 1) and (qlist[1] > ""): 
                    dialog = xbmcgui.Dialog()
                    index_ = dialog.select(title, qlist)
                    if int(index_) < 0:
                        index_ = 0    
                else:
                    index_ = 0 
        url_ = url_.replace('[' + qualities + ']', qlist[int(index_)])
    return index_, url_

def showSerial(content, url, image):
    for i, season in enumerate(content):
        title = season['comment']
        uri = sys.argv[0] + '?mode=show&url=' + url + '&season=' + str(i) 
        item = xbmcgui.ListItem(title, thumbnailImage=image)
        xbmcplugin.addDirectoryItem(pluginhandle, uri, item, True)

def showSeason(content, title, genre, image, desc):
    index = None
    for episode in content:
        title = ('%s') % (episode['comment'])
        url = episode['file']
        # select quality
        index, url = selectQuality(url, index, "") 

        uri = sys.argv[0] + '?mode=play&url=%s' % url

        item = xbmcgui.ListItem(title, thumbnailImage=image)
        info = {"Title": title, 'genre' : genre, "Plot": desc, "overlay": xbmcgui.ICON_OVERLAY_WATCHED, "playCount": 0}
        item.setInfo( type='Video', infoLabels=info)
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(pluginhandle, uri, item, False)

def showItem(url, thumbnail, season = None):
    content = common.fetchPage({"link": url})["content"]
    mainf = common.parseDOM(content, "div", attrs = { "class":"categ" })
    block = common.parseDOM(content, "div", attrs = { "class":"ssc" })[0]

    image_container = common.parseDOM(block, "td", attrs = { 'valign':'top' })
    image = common.parseDOM(image_container, "img", ret="src")[0]
    image = image if image.startswith( 'http' ) else BASE_URL + image

    genre = unescape(" ".join(str(g) for g in common.parseDOM(mainf, "a")), 'cp1251')

    title = beatify_title(getTitle(block))
    desc = common.stripTags(getDescription(block))

    playlist = common.parseDOM(content, 'input', attrs = { "name": "pl"}, ret="value")[0]

    if playlist:
        response = common.fetchPage({"link":playlist})["content"]

        try:
          playlist = json.loads(response)['playlist']
        except ValueError:
          print "WARNING: wrong JSON format"

          response = response.replace('\r', '').replace('\t', '').replace('\r\n', '')
          playlist = json.loads(response)['playlist']

        if ('playlist' in playlist[0]) and (season == None):
            print "*** This is a playlist with several seasons"
            showSerial(playlist, url, image)            
        else:
            print "*** This is a playlist with one season"
            content = playlist if (season == None) else playlist[int(season)]['playlist']
            showSeason(content, title, genre, image, desc) 

    try:
        mode = VIEW_MODES[Addon.getSetting('episodsViewMode')]
        xbmc.executebuiltin("Container.SetViewMode(" + mode +")")
    except Exception, e:
        print "*** Exception"
        print e
        xbmc.executebuiltin('Container.SetViewMode(50)')

    xbmcplugin.endOfDirectory(pluginhandle, True)

def playItem(url):
    print url
    item = xbmcgui.ListItem(path = url)
    item.setProperty('mimetype', 'video/x-flv')
    xbmcplugin.setResolvedUrl(pluginhandle, True, item)


# MAIN()
params = get_params()

# TODO: code refactoring
url=None
mode=None
categorie=None
thumbnail=None
page=None
season=None

bestquality = Addon.getSetting('quality') if Addon.getSetting('quality') else "false"

try:
    mode=params['mode'].upper()
except: pass
try:
    url=urllib.unquote_plus(params['url'])
except: pass
try:
    categorie=params['categorie']
except: pass
try:
    thumbnail=urllib.unquote_plus(params['thumbnail'])
except: pass
try:
    page=params['page']
except: pass
try:
    season=params['season']
except: pass

keyword = params['keyword'] if 'keyword' in params else None
external = 'unified' if 'unified' in params else None
if external == None:
    external = 'usearch' if 'usearch' in params else None    
transpar = params['translit'] if 'translit' in params else None

if mode == 'RNEXT':
    getRecentItems(url)
elif mode == 'CATEGORIES':
    getCategories(BASE_URL)
elif mode == 'CATEGORIE':
    getCategoryItems(url, categorie, '1')
elif mode == 'CNEXT':
    getCategoryItems(url, categorie, page)
elif mode == 'SHOW':
    showItem(url,thumbnail,season)
elif mode == 'PLAY':
    playItem(url)
elif mode == 'GENRES':
    listGenres()
elif mode == 'SEARCH':
    search(keyword, external, transpar)
elif mode == 'FAVORITES':
    listFavorites()
elif mode == 'RESET':
    resetFavorites()
elif mode == None:
    url = BASE_URL if url == None else url
    getRecentItems(url)

# View modes
# <include>CommonRootView</include> <!-- view id = 50 -->
# <include>FullWidthList</include> <!-- view id = 51 -->
# <include>ThumbnailView</include> <!-- view id = 500 -->
# <include>PosterWrapView</include> <!-- view id = 501 -->
# <include>PosterWrapView2_Fanart</include> <!-- view id = 508 -->
# <include>MediaListView3</include> <!-- view id = 503 -->
# <include>MediaListView2</include> <!-- view id = 504 -->
# <include>WideIconView</include> <!-- view id = 505 -->
# <include>MusicVideoInfoListView</include> <!-- view id = 511 -->
# <include>AddonInfoListView1</include> <!-- view id = 550 -->
# <include>AddonInfoThumbView1</include> <!-- view id = 551 -->
# <include>LiveTVView1</include> <!-- view id = 560 -->
