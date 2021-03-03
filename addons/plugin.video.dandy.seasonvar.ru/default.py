#!/usr/bin/python
# -*- coding: utf-8 -*-
# Writer (c) 2014-2017, dandy, MrStealth
# Rev. 1.7.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import sys
import socket
import json
import re
from urllib.request import Request, build_opener, HTTPCookieProcessor, HTTPHandler
import http.cookiejar

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import XbmcHelpers
common = XbmcHelpers

import Translit as translit
translit = translit.Translit()

socket.setdefaulttimeout(120)

Addon = xbmcaddon.Addon(id='plugin.video.dandy.seasonvar.ru')

import xppod
Decoder = xppod.XPpod(Addon)

try:
    sys.path.append(os.path.dirname(__file__)+ '/../plugin.video.unified.search')
    from unified_search import UnifiedSearch
except:
    pass

# Filter consts
FILTER_TYPE_GENRES = 0
FILTER_TYPE_COUNTRIES = 1
FILTER_TYPE_YEARS = 2
FILTER_TYPES = ((0, 1, 2), ('genre', 'country', 'year'), ('quotG', 'quotC', 'quotY'))
WINDOW_VIDEO_NAV = 10025

class SeasonvarTranslators():

    def __init__(self, data_path):
        self.data_path = data_path
        
        self.data = {}
        if os.path.exists(self.data_path):
            try:
                self.data = json.load(open(self.data_path))
            except:
                pass

    def remove(self, item_id):
        if not item_id in self.data:
            return
            
        del self.data[item_id]

        self.save()

    def add(self, item_id, translator):
        self.data[item_id] = translator

        self.save()

    def save(self):
        json.dump(self.data, open(self.data_path, "w"))

    def contains(self, item_id):
        return item_id in self.data

    def get(self, item_id):
        return self.data[item_id]

class Seasonvar():

    def __init__(self):
        self.id = 'plugin.video.dandy.seasonvar.ru'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')
        self.data_path = os.path.join(self.path, 'data')

        if not (os.path.exists(self.data_path) and os.path.isdir(self.data_path)):
            os.makedirs(self.data_path)

        self.language = self.addon.getLocalizedString

        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.url = self.addon.getSetting('domain')

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.debug = False

        self.begin_render_type = self.addon.getSetting('begin_render_type') if self.addon.getSetting('begin_render_type') else None        
        self.load_thumbnails = self.addon.getSetting('load_thumbnails') if self.addon.getSetting('load_thumbnails') else None
        self.new_search_method = self.addon.getSetting('new_search_method') if self.addon.getSetting('new_search_method') else None
        self.quality = self.addon.getSetting('quality') if self.addon.getSetting('quality') else "sd"
        self.translator = self.addon.getSetting('translator') if self.addon.getSetting('translator') else "standard"
        self.addtolib = self.addon.getSetting('addtolib') if self.addon.getSetting('addtolib') else None

        self.authcookie = ''        
        self.vip = False
        self.cookie=self.addon.getSetting('cookie') if self.addon.getSetting('cookie') else None 
        if self.cookie and (self.cookie > ''):
            self.authcookie = "svid1=" + self.cookie
            self.vip = True
        
        self.headers = {
                "Host" : self.url.split("://")[1],
                "Connection" : "keep-alive",
                "X-Requested-With" : "XMLHttpRequest",
                "Referer" : self.url,
                "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:35.0) Gecko/20100101 Firefox/35.0"
                }    
                
        # cache
        self.contentMain   = ''
        self.contentBegin  = None                
        self.contentFilter = None     

        self.addplaylists = []
        
        self.translators = SeasonvarTranslators(os.path.join(self.data_path, "translators.json"))
        
        #self.login()

    def getMainContent(self):
        if self.contentMain == "":
            response = common.fetchPage({"link": self.url})
            if response["status"] == 200:
                self.contentMain = response["content"].decode("utf-8")
        return self.contentMain

    def login(self):
        print("*** Login")
        login = self.addon.getSetting('login')
        if login:
            password = self.addon.getSetting('password')
            headers = {
                "Host" : self.url.split("://")[1],
                "Referer" : self.url + '/',
                "Origin" : self.url,
                "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"
                }                    
            values = {
                "login": login,
                "password": password
                }
        
            cj = http.cookiejar.CookieJar()
            opener = build_opener(HTTPCookieProcessor(cj), HTTPHandler())
            req = Request(self.url + "/?mod=login", urllib.parse.urlencode(values).encode("utf-8"), headers)
            f = opener.open(req)
            
            for cookie in cj:
                cookie = str(cookie).split('svid1=')[-1].split(' ')[0].strip()
                if cookie and (cookie > ""):
                    self.addon.setSetting('cookie', cookie)
                    #self.authcookie = "svid1=" + cookie
                    #self.vip = True

    def main(self):
        self.log("Addon: %s"  % self.id)
        self.log("Handle: %d" % self.handle)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)

        mode = params['mode'] if 'mode' in params else None
        url = urllib.parse.unquote_plus(params['url']) if 'url' in params else None

        keyword = urllib.parse.unquote_plus(params['keyword']) if 'keyword' in params else None
        external = 'unified' if 'unified' in params else None
        if external == None:
            external = 'usearch' if 'usearch' in params else None    
        transpar = params['translit'] if 'translit' in params else None
        strong = params['strong'] if 'strong' in params else None

        withMSeason = params['wm'] if 'wm' in params else "1"
        idPlaylist = int(params['idpl']) if 'idpl' in params else 0

        page = int(params['page']) if 'page' in params else None
        if page == 0:	
            xbmc.executebuiltin('Container.Update(%s, replace)' % sys.argv[0])

        filterType = int(params['ft']) if 'ft' in params else None
        filterValue = params['fv'] if 'fv' in params else None
        alphaBeta = int(params['ab']) if 'ab' in params else 0   
      
        title =  urllib.parse.unquote_plus(params['title']) if 'title' in params else None
        
        if mode == 'play':
            self.playItem(params['serial'], params['season'], params['episode'])
        elif mode == 'tranalation':
            season_id = self.getSeasonIdFromLink(url)
            if season_id:
                self.translators.remove(season_id)

            self.show(url, title, (withMSeason == "1"))
        elif mode == 'search':
            self.search(keyword, external, transpar, strong)
        elif mode == 'show':
            self.show(url, title, (withMSeason == "1"))
        elif mode == 'filter':
            self.getFilter(filterType, filterValue, alphaBeta)
        elif mode == 'nextdate':
            self.getItemsByDate(page)
        elif mode == 'playlist':
            self.partPlaylist(url, idPlaylist)
        elif mode in ['paused', 'wishlist', 'history']:
            self.mainMenu(mode)
        else:
            self.mainMenu()

    def mainMenu(self, itemsSourse = None):
        #self.addon.setSetting('cookie', '')
        self.login()
        self.cookie=self.addon.getSetting('cookie') if self.addon.getSetting('cookie') else None 
        if self.cookie and (self.cookie > ''):
            self.authcookie = "svid1=" + self.cookie
            self.vip = True

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(2000))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s' % ("filter")
        item = xbmcgui.ListItem("[COLOR=FF7B68EE]%s[/COLOR]" % self.language(3000))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })        
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        if self.vip:
            uri = sys.argv[0] + '?mode=%s' % ("paused")
            item = xbmcgui.ListItem("[COLOR=FF7B68EE]%s[/COLOR]" % self.language(7000))
            item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            uri = sys.argv[0] + '?mode=%s' % ("wishlist")
            item = xbmcgui.ListItem("[COLOR=FF7B68EE]%s[/COLOR]" % self.language(7001))
            item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            uri = sys.argv[0] + '?mode=%s' % ("history")
            item = xbmcgui.ListItem("[COLOR=FF7B68EE]%s[/COLOR]" % self.language(7002))
            item.setArt({ 'thumb': self.icon, 'icon' : self.icon })            
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.getItems(itemsSourse)

        xbmcplugin.setContent(self.handle, 'tvshows')
        xbmcplugin.endOfDirectory(self.handle, True)
        
    def getSerialImage(self, url):
        if (not self.load_thumbnails) or (self.load_thumbnails == "false"):
            return self.icon
        else:    
            #response = common.fetchPage({"link": url})            
            #image = response["content"].split('<meta property="og:image" content="')[-1].split('">')[0]
            image = "http://cdn." + self.url.split("://")[1] + "/oblojka/%s.jpg" % (url.split("serial-")[-1].split("-")[0])
            return image if image else self.icon

    def getItemsByDate(self, page):
        if (not self.contentBegin) or (page == 0):
            data = self.getMainContent().split('<div class="content-wrap">')[-1].split('</body>')[0]
            self.contentBegin = data
        else:
            data = self.contentBegin

        dateitems = common.parseDOM(data, "div", attrs={"class": "news"})
        count = len(dateitems)
        dateitemnext = None
        
        try:
            dateitem = dateitems[page]
        except:
            return

        filmitems = common.parseDOM(dateitem, "a")
        urls = common.parseDOM(dateitem, "a", ret = "href")
        for i, filmitem in enumerate(filmitems):
            titlediv = common.parseDOM(filmitem, "div", attrs={"class": "news-w"})[0]
            title = self.strip(common.parseDOM(titlediv, "div", attrs={"class": "news_n"})[0])
            titleadd = common.parseDOM(titlediv, "span", attrs={"class": "news_s"})[0]
            title_ = title + ' [COLOR=FF00FFF0][' + titlediv.split('</div>')[-1].split('<span')[0].strip() + " " + titleadd + '][/COLOR]'
            link = urls[i]
            uri = sys.argv[0] + '?mode=show&url=%s&title=%s&wm=0' % (self.url + link, title)
            image = self.getSerialImage(self.url + link)
            item = xbmcgui.ListItem(title_)
            item.setArt({ 'thumb': image, 'icon' : image })
            item.setInfo(type='Video', infoLabels={'title': title_})
            commands = []
            uricmd = sys.argv[0] + '?mode=search&keyword=%s&strong=1' % (title.split('/')[0].strip())
            commands.append((self.language(2000), "Container.Update(%s)" % (uricmd), ))

            self.addTranslationMenuItem(commands, self.url + link, title)

            item.addContextMenuItems(commands)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            
        if page > 0:
            uri = sys.argv[0] + '?page=%s' % ("0")
            item = xbmcgui.ListItem('[COLOR=FFFFD700]' + self.language(9001) + '[/COLOR]')
            item.setArt({ 'thumb': self.inext, 'icon' : self.inext })            
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            
        if (page + 1) < count:
            dateitemnext = dateitems[page+1]       
            date = common.parseDOM(dateitemnext, "div", attrs={"class": "news-head"})[0]            
            uri = sys.argv[0] + '?mode=%s&page=%s' % ("nextdate", str(int(page) + 1))
            item = xbmcgui.ListItem('[COLOR=FFFFD700]' + self.language(9000) % (date) + '[/COLOR]')
            item.setArt({ 'thumb': self.inext, 'icon' : self.inext })
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'tvshows')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getItems(self, itemsSourse = None, page = 0):
        print("*** Get items")
        content = None

        values = {
            "ganre": "",
            "country": "",
            "block": "0",
            "main": "1"
        }

        if itemsSourse is None:
            itemsSourse = self.begin_render_type

        if (itemsSourse == None) or (itemsSourse == 'new'):
            url_ = self.url + '/ajax.php?mode=new'
        elif (itemsSourse == 'popular'):
            url_ = self.url + '/ajax.php?mode=pop'
        elif (itemsSourse == 'newest'):
            url_ = self.url + '/ajax.php?mode=newest'
        elif itemsSourse in ['paused', 'wishlist']:
            url_ = self.url + '/?mod=pause'
            values.clear()
        elif itemsSourse == 'history':
            url_ = self.url + '/?mod=history'
            values.clear()
        elif (itemsSourse == 'bydate'):
            self.getItemsByDate(page)
            return
        else:
            url_ = self.url + '/ajax.php?mode=new'
            
        headers = {
            "Cookie": self.getCookies(),
            "Host" : self.url.split("://")[1],
            "Origin": self.url,
            "Connection" : "keep-alive",
            "X-Requested-With" : "XMLHttpRequest",
            "Referer" : self.url + "/",
            "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:35.0) Gecko/20100101 Firefox/35.0"
        }

        request = urllib.request.Request(url_, urllib.parse.urlencode(values), headers)
        content = urllib.request.urlopen(request).read()            

        if itemsSourse == 'paused':
            items = self.parsePaused(content, "marks-new")
        elif itemsSourse == 'wishlist':
            items = self.parsePaused(content, 'marks-want')
        elif itemsSourse == 'history':
            items = self.parseHistory(content)
        else:
            items = self.parseSidebar(content)

        for item in items:

            uri = sys.argv[0] + '?mode=show&url=%s&title=%s&wm=0' % (item["link"], item["title"])
            list_item = xbmcgui.ListItem(item["title_full"])
            list_item.setArt({ 'thumb': item["image"], 'icon' : item["image"] })
            list_item.setInfo(type='Video', infoLabels={'title': item["title_full"]})

            commands = []
            uricmd = sys.argv[0] + '?mode=search&url=%s&keyword=%s&strong=1' % (self.url, item["title"].split('/')[0].strip())                
            commands.append((self.language(2000), "Container.Update(%s)" % (uricmd), ))

            self.addTranslationMenuItem(commands, item["link"], item["title"])

            list_item.addContextMenuItems(commands)

            xbmcplugin.addDirectoryItem(self.handle, uri, list_item, True)
        
        xbmcplugin.setContent(self.handle, 'tvshows')
        xbmcplugin.endOfDirectory(self.handle, True)
            
    def parseHistory(self, content):

        if not content:
            return []

        items_container = common.parseDOM(content, "div", attrs={"class": "pgs-history-c"})
        if len(items_container) != 1:
            return []

        history_items = []

        items = common.parseDOM(items_container[0], "a")
        urls = common.parseDOM(items_container[0], "a", ret="href")

        for i, item in enumerate(items):
            
            title = common.parseDOM(item, "b")[0]
            titleadd = item.split('</b>')[1]
            title_ = self.strip(title + ' [COLOR=FF00FFF0][' + titleadd + '][/COLOR]')
            title_ = ' '.join(title_.split()).strip()

            history_item = {
                "title": title,
                "title_full": title_,
                "image": self.getSerialImage(urls[i]),
                "link": self.url + urls[i]
            }

            history_items.append(history_item)

        return history_items

    def parsePaused(self, content, tab_id):

        if not content:
            return []

        items_container = common.parseDOM(content, 'li', attrs={'data-tabr': tab_id})
        if len(items_container) != 1:
            return []

        paused_items = []

        items = common.parseDOM(items_container[0], "div", attrs={"class": "pgs-marks-el"})

        for i, item in enumerate(items):
            
            urls = common.parseDOM(item, "a", ret="href")
            titlediv = common.parseDOM(item, "div", attrs={"class": "pgs-marks-txt"})[0]
            title = common.parseDOM(titlediv, "div", attrs={"class": "pgs-marks-name"})[0]
            titleadd = self.strip(common.parseDOM(titlediv, "div", attrs={"class": "pgs-marks-current"})[0].replace('<br>', ','))
            title_ = self.strip(title + ' [COLOR=FF00FFF0][' + titleadd + '][/COLOR]')
            title_ = ' '.join(title_.split()).strip()

            paused_item = {
                "title": title,
                "title_full": title_,
                "image": self.getSerialImage(urls[0]),
                "link": urls[0]
            }

            paused_items.append(paused_item)

        return paused_items

    def parseSidebar(self, content):
        if not content:
            return []

        sidebar_items = []

        items = common.parseDOM(content, "a", attrs={"class": "pst rside-p"})
        urls = common.parseDOM(content, "a", attrs={"class": "pst rside-p"}, ret="href")

        for i, item in enumerate(items):
            
            titlediv = common.parseDOM(item, "div", attrs={"class": "rside-d"})[0]
            title = common.parseDOM(titlediv, "div", attrs={"class": "rside-t"})[0]
            titleadd = self.strip(common.parseDOM(titlediv, "div", attrs={"class": "rside-ss"})[0].replace('<br>', ','))
            title_ = self.strip(title + ' [COLOR=FF00FFF0][' + titleadd + '][/COLOR]')
            title_ = ' '.join(title_.split()).strip()

            sidebar_item = {
                "title": title,
                "title_full": title_,
                "image": common.parseDOM(item, "img", ret="data-src")[0],
                "link": self.url + urls[i]
            }

            sidebar_items.append(sidebar_item)

        return sidebar_items

    def addTranslationMenuItem(self, commands, url, title):

        if self.translator == "standard":
            return

        uricmd = sys.argv[0] + '?mode=tranalation&url=%s&title=%s&wm=0' % (url, title)

        cmd_title = self.language(6000)
        season_id = self.getSeasonIdFromLink(url)
        if season_id and self.translators.contains(season_id):
            cmd_title += " (%s)" % self.translators.get(season_id)

        commands.append((cmd_title, "Container.Update(%s)" % (uricmd), ))

    def getSeasonIdFromLink(self, link):
        chunks = link.split('-')

        if len(chunks) < 2:
            return None

        return chunks[1] 

    def getCookies(self):
        sc = ""
        if self.vip == True:
            sc = self.authcookie
            if self.quality == "sd":
                sc += "; hdq=1"
        return sc

    def getParamsForRequestPlayList(self, content):
        idseason = common.parseDOM(content, 'div', attrs={'class': 'pgs-sinfo'}, ret='data-id-season')[0]
        idserial = common.parseDOM(content, 'div', attrs={'class': 'pgs-sinfo'}, ret='data-id-serial')[0]
        div = common.parseDOM(content, 'div', attrs={'class': 'pgs-player'})[0]
        secure = div.split("'secureMark': '")[-1].split("',")[0]
        return idseason, idserial, secure

    def selectTranslator(self, content, id_season):

        playlist0 = content.split('<script>var pl = {\'0\': "')[-1].split('"};</script>')[0]
        try:
            div = common.parseDOM(content, 'ul', attrs={'class': 'pgs-trans'})[0]
        except:
            return playlist0 
        titles = common.parseDOM(div, 'li', attrs={'data-click': 'translate'})
        playlists = common.parseDOM(div, 'script')

        if len(titles) > 1:

            index_ = -1

            if self.translators.contains(id_season):
                translator = self.translators.get(id_season)
                if translator in titles:
                    index_ = titles.index(translator)

            if int(index_) < 0:
                dialog = xbmcgui.Dialog()
                index_ = dialog.select(self.language(6000), titles)

            if int(index_) < 0:
                index_ = 0
            else:
                self.translators.add(id_season, titles[index_])
        else:
            index_ = 0
            
        playlist = playlist0 if index_ == 0 else playlists[index_-1]
        playlist = playlist.split('] = "')[-1].split('";')[0]

        return playlist

    def getURLPlayListFromContent(self, content, kind, idseason):
        if (kind == 0):
            if self.translator == "standard":
                playlist = content.split('<script>var pl = {\'0\': "')[-1].split('"};</script>')[0]
            else:
                playlist = self.selectTranslator(content, idseason) 
        elif (kind == 2):
            playlist = content.split('<script>var pl = {\'0\': "')[-1].split('"};</script>')[0]
        else:
            playlist = content.split('<script>pl[68] = "')[-1].split('";</script>')[0]
        return self.url + playlist   
        
    def getURLPlayList(self, url, content, kind):

        idseason, idserial, secure = self.getParamsForRequestPlayList(content)
        
        headers = {
            "Cookie": self.getCookies(),
            "Host": self.url.split("://")[1],
            "Origin": self.url,
            "Referer": url,
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }

        values = {
            "id": idseason,
            "serial": idserial,
            "type": "html5",
            "secure": secure
        }

        request = Request(self.url + "/player.php", urllib.parse.urlencode(values).encode("utf-8") , headers)
        content = urllib.request.urlopen(request).read().decode("utf-8")

        return self.getURLPlayListFromContent(content, kind, idseason)
        
    def partPlaylist(self, url, idPlaylist):
        response = common.fetchPage({"link": url, "cookie": self.getCookies()})
        image = common.parseDOM(response["content"].decode("UTF-8"), 'link', attrs={'rel': 'image_src'}, ret='href')[0] if common.parseDOM(response["content"].decode("UTF-8"), 'link', attrs={'rel': 'image_src'}, ret='href') else None
        description = common.parseDOM(response["content"].decode("UTF-8"), 'meta', attrs={'name': 'description'}, ret='content')[0] if common.parseDOM(response["content"].decode("UTF-8"), 'meta', attrs={'name': 'description'}, ret='content') else ''
        
        idseason, idserial, secure = self.getParamsForRequestPlayList(response["content"].decode("UTF-8"))
        response = common.fetchPage({"link": self.getURLPlayList(url, response["content"].decode("UTF-8"), 2), "cookie": self.getCookies()})
        
        json_playlist = json.loads(response["content"].decode("UTF-8"))
        playlist = json_playlist[idPlaylist]
        playlist_ = playlist['folder']

        self.parsePlaylist(url, playlist_, image, description, "", "", "", idserial)

        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getTitle(self, title1, title2, title3, season, mode = 0):
        if self.addtolib != "false":
            return title3 + " S" + season.zfill(2) + "E" + title2.split(" ")[0].zfill(2) + " [" + title2.replace(title2.split(" ")[0], "").strip().replace(title2.split(" ")[1], "").strip() + "]"
        elif mode == 0:
            return title2
        else:
            return title1 + " " + title2

    def parsePlaylist(self, season_url, playlist, image, description, title, season, title_orig, idserial):

        win = xbmcgui.Window(WINDOW_VIDEO_NAV)

        for episode in playlist:
            etitle = self.strip(episode['title'].replace("<br>", "  "))
            playlist_ = None
            
            url = self.decodeEpisodeFileURL(episode)

            if not url:
                playlist_ = episode['folder']

            if playlist_:
                self.addplaylists.append(playlist_)
                uri = sys.argv[0] + '?mode=playlist&url=%s&idpl=%d' % (season_url, (len(self.addplaylists)-1))
                item = xbmcgui.ListItem('[COLOR=FFFFD700]' + etitle + '[/COLOR]')
                item.setArt({ 'thumb': image, 'icon' : image })
                item.setInfo(type='Video', infoLabels={'title': etitle})
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            else:    

                itemid = episode['galabel'] # ИД сериала + ИД серии, глобально уникальный 
                season_doc = season_url.split("/")[-1]
                season_doc = season_doc.split("#")[0]

                uri = sys.argv[0] + '?mode=play&serial=%s&season=%s&episode=%s' % (idserial, season_doc, itemid)
                sub_name = None
                subtitle = None
                try:
                    sub_name = episode["subtitle"].split(']')[0].replace('[', '')
                    subtitle = episode["subtitle"].split(']')[1]
                except:
                    pass
                item = xbmcgui.ListItem(label=self.getTitle(title, etitle, title_orig, season))
                item.setArt({ 'thumb': image, 'icon' : image })

                labels = {'title': self.getTitle(title, etitle, title_orig, season, 1), 'plot': description}
                
                win.setProperty("seasonvar_real_url_" + itemid, url)

                item.setInfo(type='Video', infoLabels=labels)
                item.setProperty('IsPlayable', 'true')
                if subtitle and (subtitle != ''):
                    item.setSubtitles([subtitle])
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)            

    def getPlaylistByUppod(self, content):
        divplayer = common.parseDOM(content, 'div', attrs={'id': 'videoplayer719'})
        hashdiv = common.parseDOM(divplayer, "script", attrs={"type": "text/javascript"})[0]
        uhash = hashdiv.split('var pl0 = "')[-1].split('";')[0] if 'var pl0 = "' in hashdiv else None
        pl_url = Decoder.Decode_String(uhash, 'JpvnsR03Tmwu9xgaGLUXztb7H=' + '\n' + 'fNW5elVDyZIiMoQ1B826cd4YkC')
        response = common.fetchPage({"link": self.url + pl_url})
        json_playlist = json.loads(response["content"].decode("utf-8"))
        playlist = json_playlist['playlist']
        if not playlist:
            hashdiv = common.parseDOM(divplayer, "div", attrs={"id": "translateDivParent"})[0]
            uhash = hashdiv.split('var pl68 = "')[-1].split('";')[0] if 'var pl68 = "' in hashdiv else None
            pl_url = Decoder.Decode_String(uhash, 'JpvnsR03Tmwu9xgaGLUXztb7H=' + '\n' + 'fNW5elVDyZIiMoQ1B826cd4YkC')                
            response = common.fetchPage({"link": self.url + pl_url})
            json_playlist = json.loads(response["content"].decode("utf-8"))
            
    def checkAccessContent(self, content):
            bad = common.parseDOM(content, 'div', attrs={'class': 'pgs-player-block'})
#            if not bad:
#                bad = common.parseDOM(content, 'div', attrs={'class': 'pgs-msg'})
            if bad:
                self.showErrorMessage("Content unavailable")
                return False
            else:    
                return True

    def getMultiseasonDiv(self, content):
        return common.parseDOM(content, 'div', attrs={'class': 'pgs-seaslist'})

    def show(self, url, title, withMSeason = True):
        print("*** show for url %s " % url)

        response = common.fetchPage({"link": url, "cookie": self.getCookies()})
        
        content = response["content"].decode("UTF-8")
        titlemain = common.parseDOM(content, 'title')[0]
        image = common.parseDOM(content, 'meta', attrs={'property': 'og:image'}, ret='content')[0] if common.parseDOM(content, 'meta', attrs={'property': 'og:image'}, ret='content') else None
        description = common.parseDOM(content, 'meta', attrs={'name': 'description'}, ret='content')[0] if common.parseDOM(response["content"].decode("utf-8"), 'meta', attrs={'name': 'description'}, ret='content') else ''
        multiseason = self.getMultiseasonDiv(content)
        title_orig_div = common.parseDOM(content, 'div', attrs={'class': 'pgs-sinfo_list'})[0]
        title_orig = common.parseDOM(title_orig_div, 'span')[0].replace("&#039;", "'")
        title_ = common.parseDOM(content, 'meta', attrs={'property': 'og:title'}, ret='content')[0]
        parts = title_.split(" ")
        season = None
        for i, part in enumerate(parts):
            if "сезон" in part:
                season = parts[i-1]
        if season == None:
            season = "1"

        if withMSeason and multiseason:
            serialitems = common.parseDOM(multiseason, "h2")
            for serialitem in serialitems:
                url = self.url + common.parseDOM(serialitem, "a", ret="href")[0]
                title = common.parseDOM(serialitem, "a")[0]
                title = title.replace('<span>', '[COLOR=FF00FFF0][').replace('</span>', '][/COLOR]').replace('<small>', '[COLOR=FF00FFF0][').replace('</small>', '][/COLOR]').replace("&#039;", "'")
                title = ' '.join(title.split()).strip()
                uri = sys.argv[0] + '?mode=show&url=%s&title=%s&wm=0' % (url, title)
                item = xbmcgui.ListItem(self.strip(title))
                item.setArt({ 'thumb': image, 'icon' : image })
                item.setInfo(type='Video', infoLabels={'title': title})
                item.select(title.find('>>>') > -1)

                commands = []

                self.addTranslationMenuItem(commands, url, title)

                item.addContextMenuItems(commands)

                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
           
        else:
            playlist = self.extractPlaylist(url, content)

            idseason, idserial, secure = self.getParamsForRequestPlayList(content)
            self.parsePlaylist(url, playlist, image, description, title, season, title_orig, idserial)

        if withMSeason and multiseason:
           xbmcplugin.setContent(self.handle, 'files')
        else:
           xbmcplugin.setContent(self.handle, 'episodes')

        xbmcplugin.endOfDirectory(self.handle, True)

        focus_on = None
        if "#rewind=" in url:
            focus_on = url.split("#rewind=")[1]

            focus_on = focus_on.split("_")[0]

            xbmc.sleep(100)
            win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            cid = win.getFocusId()

            ctl = win.getControl(cid)
            ctl.selectItem(int(focus_on))


    def decodeEpisodeFileURL(self, episode):
        try:
            regex = r"(\/\/.*?=)"
            url = re.sub(regex, '', episode['file'])
            import base64
            url = base64.b64decode(url[2:]).decode("utf-8")
            url = url.split(" ")[0]
            return url
        except Exception as e:
            self.log("Exception: %s" % str(e))
            return ""


    def extractPlaylist(self, url, content = None):

        if content is None:
            response = common.fetchPage({"link": url, "cookie": self.getCookies()})
            content = response["content"].decode("UTF-8")

        if not self.checkAccessContent(content):
            return []

        self.addplaylists = []

        try: 
            response = common.fetchPage({"link": self.getURLPlayList(url, content, 0), "cookie": self.getCookies()})
            json_playlist = json.loads(response["content"].decode("UTF-8"))
        except Exception as e:
            self.showErrorMessage("Content unavailable")
            return []

        playlist = json_playlist

        if not playlist:
            try:
                response = common.fetchPage({"link": self.getURLPlayList(url, content, 1), "cookie": self.getCookies()})
                json_playlist = json.loads(response["content"].decode("UTF-8"))

                if type(json_playlist) is dict:
                    playlist = json_playlist['playlist']
                elif type(json_playlist) is list:
                    playlist = json_playlist
                else:
                    raise ValueError("Content unavailable")

            except Exception as e:
                self.showErrorMessage("Content unavailable")
                return []

        return playlist

    def updateSiteHistory(self, season_url, serial_id, season_id, file_id):

        headers = self.headers
        headers["Cookie"] = self.getCookies()
        headers["Referer"] = season_url

        values = {
            "id_season": season_id,
            "file_id": file_id,
            "serial_id": serial_id,
            "svid1": self.cookie,
            "idTrans": 0 # неважно
        }

        request = urllib.request.Request(self.url + "/plStat.php", urllib.parse.urlencode(values).encode("utf-8"), headers)
        content = urllib.request.urlopen(request).read().decode("utf-8")

    def playItem(self, serial, season, episode):
        print("*** play id %s" % episode)

        window = xbmcgui.Window(WINDOW_VIDEO_NAV)

        season_url = self.url +  '/' +  season

        episode_url = window.getProperty("seasonvar_real_url_" + episode)

        if not episode_url:
            playlist = self.extractPlaylist(season_url)

            for item in playlist:
                if episode == item['galabel']:
                    episode_url = self.decodeEpisodeFileURL(item)
                    break

            if not episode_url:
                return

        if self.vip:
            (season_id, file_id) = episode.split("_")			
            self.updateSiteHistory(season_url, serial, season_id, file_id)

        item = xbmcgui.ListItem(path=episode_url)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def USTranslit(self, keyword, transpar):
        return translit.rus(keyword) if (transpar == None) or (transpar == "true") else keyword

    def getUserInput(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(4000))
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            if self.addon.getSetting('translit') == 'true':
                keyword = translit.rus(kbd.getText())
            else:
                keyword = kbd.getText()

        return keyword

    def newSearchMethod(self, keyword, external, unified_search_results, strong):
        url = self.url +  '/search?' +  urllib.parse.urlencode({"q" : keyword})

        response = common.fetchPage({"link": url})
        data =  response["content"].decode("utf-8")
        searchitems = common.parseDOM(data, 'div', attrs={'class': 'pgs-search-wrap'})
        for searchitem in searchitems:
            url = self.url + common.parseDOM(searchitem, "a", ret="href")[0]
            image = common.parseDOM(searchitem, "img", ret="src")[0]
            titlediv = common.parseDOM(searchitem, "div", attrs={"class": "pgs-search-info"})
            title = common.parseDOM(titlediv, "a")[0]
            seasons = common.parseDOM(titlediv, "span")
            descr = common.parseDOM(titlediv, "p")[0]
            if (not strong) or (keyword.upper() == title.decode('utf-8').upper()): 
                if seasons:
                    title = title + ' [COLOR=FF00FFF0][' + seasons[0] + '][/COLOR]'                  
            
                if (external == 'unified'):
                    self.log("Perform unified search and return results")
                    unified_search_results.append({'title': title, 'url': url, 'image': image, 'plugin': self.id})
                else:
                    uri = sys.argv[0] + '?mode=show&url=%s&wm=1' % url
                    item = xbmcgui.ListItem(title)
                    item.setArt({ 'thumb': image, 'icon' : image })
                    item.setInfo(type='Video', infoLabels={'title': title, 'plot': descr})

                    commands = []

                    self.addTranslationMenuItem(commands, url, title)

                    item.addContextMenuItems(commands)

                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

    def search(self, keyword, external, transpar = None, strong = None):
        print("*** search for keyword %s " % keyword)
        
        keyword_ = keyword if keyword else self.getUserInput()
        if keyword_: 
            keyword_ = self.USTranslit(keyword_, transpar) if (external == 'unified') else keyword_
            keyword_ = keyword_ if isinstance(keyword_, str) else str(keyword_)
        else:
           return 
        
        unified_search_results = []
        
        if keyword_:
            if self.new_search_method and (self.new_search_method == "true"):
                self.newSearchMethod(keyword_, external, unified_search_results, strong)
            else:

                url = self.url + '/autocomplete.php?' + urllib.parse.urlencode({"query" : keyword_})
                response = common.fetchPage({"link": url})
                count = 1
                s = json.loads(response["content"].decode("utf-8"))
                count = len(s['suggestions'])
                if count < 1: return False
                
                for i in range(0, count):
                    title = s['suggestions'][i].encode('utf-8')
                    surl = s['data'][i]
                    if surl.find('.html') > -1:
                        url = self.url + '/' + s['data'][i]
                        if (external == 'unified'):
                            self.log("Perform unified search and return results")
                            unified_search_results.append({'title': title, 'url': url, 'image': self.icon, 'plugin': self.id})
                        else:
                            uri = sys.argv[0] + '?mode=show&url=%s&wm=1' % url
                            item = xbmcgui.ListItem(title, thumbnailImage=self.icon)
                            item.setArt({ 'icon' : self.icon })

                            commands = []

                            self.addTranslationMenuItem(commands, url, title)

                            item.addContextMenuItems(commands)

                            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if (external == 'unified'):
                UnifiedSearch().collect(unified_search_results)
            else: 
                xbmcplugin.setContent(self.handle, 'tvshows')
                xbmcplugin.endOfDirectory(self.handle, True)

        else:
            self.menu()

    def getFilterPrefix(self, filterType):
        return FILTER_TYPES[1][filterType]

    def getFilterTypeList(self, filterType):
        if self.contentFilter:
            content = self.contentFilter
        else:
            content = self.getMainContent().split('<div class="sidebar lside">')[-1].split('<script type="text/javascript">')[0]
            self.contentFilter = content
            
        kind = self.getFilterPrefix(filterType)
        
        filterdiv = common.parseDOM(content, "select", attrs={"data-filter": kind})[0]
        filterlist = common.parseDOM(filterdiv, "option")
        filteridlist = common.parseDOM(filterdiv, "option", ret="value")
        for i, filteritem in enumerate(filterlist):        
            fv = filteridlist[i]
            fvn = filteritem

            uri = sys.argv[0] + '?mode=filter&ft=%d&fv=%s' % (filterType, fv)

            item = xbmcgui.ListItem(fvn)
            item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
            item.setInfo(type='Video', infoLabels={'title': fvn})
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmc.executebuiltin('Container.SetViewMode(52)')
        xbmcplugin.endOfDirectory(self.handle, True)
        
    def getFilterToValues(self, filterType, filterValue):
        values = {}
        if filterValue != "all":
            values["filter[" + FILTER_TYPES[2][filterType] + "][]"] = urllib.parse.unquote_plus(filterValue)
        values["filter[sortTo][]"] = "name"
        values["filter[rait]"] = "kp"                     
        return values

    def getFilterValueList(self, filterType, filterValue, alphaBeta = 0):
        values = self.getFilterToValues(filterType, filterValue)
        
        request = urllib.request.Request(self.url + "/index.php", urllib.parse.urlencode(values), self.headers)
        content = urllib.request.urlopen(request).read()

        abheaders = common.parseDOM(content, "div", attrs={"class": "letter"})
        abitems = common.parseDOM(content, "div", attrs={"data-tabgr": "letter"})
        for i, abheader in enumerate(abheaders):
            ab = common.parseDOM(abheader, "span")[0]
            if i == alphaBeta:             
                filmitems = common.parseDOM(abitems[i], "a")
                filmlinks = common.parseDOM(abitems[i], "a", ret="href")
                for j, filmitem in enumerate(filmitems):
                    try:
                        titleadd = ' [COLOR=FFFF4000][' + common.parseDOM(filmitem, "img", ret="title")[0] + '][/COLOR]'
                    except:
                        titleadd = ""
                    title = self.strip(filmitem) + titleadd
                    uri = sys.argv[0] + '?mode=show&url=%s&wm=1' % (self.url + filmlinks[j])
                    image = self.getSerialImage(self.url + filmlinks[j])
                    item = xbmcgui.ListItem(title)
                    item.setArt({ 'thumb': image, 'icon' : image })
                    item.setInfo(type='Video', infoLabels={'title': title})
                    if titleadd > "":
                        item.setProperty('IsAvailable', 'false')

                    commands = []

                    self.addTranslationMenuItem(commands, self.url + filmlinks[j], title)

                    item.addContextMenuItems(commands)
                        
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            else:
                uri = sys.argv[0] + '?mode=filter&ft=%d&fv=%s&ab=%s' % (filterType, filterValue, i)
                image = self.icon
                item = xbmcgui.ListItem('[COLOR=FFFFD700]' + ab + '[/COLOR]')
                item.setArt({ 'thumb': image, 'icon' : image })
                item.setInfo(type='Video', infoLabels={'title': ab})
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'tvshows')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getFilterList(self):
        for i, filtertype in enumerate(FILTER_TYPES[0]):
            uri = sys.argv[0] + '?mode=%s&ft=%d' % ("filter", FILTER_TYPES[0][i])
            item = xbmcgui.ListItem("%s" % self.language(4000 + FILTER_TYPES[0][i]))
            item.setArt({ 'thumb': self.icon })
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getFilter(self, filterType, filterValue, alphaBeta):
        if filterValue:
            self.getFilterValueList(filterType, filterValue, alphaBeta)
        elif filterType >= 0:
            self.getFilterTypeList(filterType)
        else:
            self.getFilterList()
            
    # *** Add-on helpers
    def log(self, message):
        if self.debug:
            print("### %s: %s" % (self.id, message))

    def error(self, message):
        print("%s ERROR: %s" % (self.id, message))

    def showErrorMessage(self, msg):
        print(msg)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(3 * 1000)))

    def strip(self, string):
        return common.stripTags(string)

    def encode(self, string):
        return string

Seasonvar = Seasonvar()
Seasonvar.main()
