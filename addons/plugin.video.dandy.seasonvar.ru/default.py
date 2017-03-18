#!/usr/bin/python
# -*- coding: utf-8 -*-
# Writer (c) 2014-2017, dandy, MrStealth
# Rev. 1.5.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import urllib
import urllib2
import sys
import socket
import json

from urllib2 import Request, build_opener, HTTPCookieProcessor, HTTPHandler
import cookielib

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
# xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("Warning", 'Please install UnifiedSearch add-on!', str(10 * 1000)))

# Filter consts
FILTER_TYPE_GENRES = 0
FILTER_TYPE_COUNTRIES = 1
FILTER_TYPE_YEARS = 2
FILTER_TYPES = ((0, 1, 2), ('selg', 'selc', 'sely'), ('quotG', 'quotC', 'quotY'))

class Seasonvar():

    def __init__(self):
        self.id = 'plugin.video.dandy.seasonvar.ru'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString

        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.url = 'http://seasonvar.ru'

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.debug = False

        self.begin_render_type = self.addon.getSetting('begin_render_type') if self.addon.getSetting('begin_render_type') else None        
        self.load_thumbnails = self.addon.getSetting('load_thumbnails') if self.addon.getSetting('load_thumbnails') else None
        self.new_search_method = self.addon.getSetting('new_search_method') if self.addon.getSetting('new_search_method') else None
        self.quality = self.addon.getSetting('quality') if self.addon.getSetting('quality') else "sd"
        
        self.headers = {
                "Host" : "seasonvar.ru",
                "Connection" : "keep-alive",
                "X-Requested-With" : "XMLHttpRequest",
                "Referer" : self.url,
                "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:35.0) Gecko/20100101 Firefox/35.0"
                }    
                
        self.authcookie = ''        
        self.vip = False
                
        # cache
        self.contentMain   = ''
        self.contentBegin  = None                
        self.contentFilter = None     

        self.addplaylists = []                   
        
        self.login()

    def getMainContent(self):
        if self.contentMain == "":
            response = common.fetchPage({"link": self.url})
            if response["status"] == 200:
                self.contentMain = response["content"]
        return self.contentMain

    def login(self):
        print "*** Login"
        
        login = self.addon.getSetting('login')
        if login:
            password = self.addon.getSetting('password')
            url = self.url + '/?mod=login'
            headers = {
                "Host" : "seasonvar.ru",
                "Connection" : "keep-alive",
                "Referer" : url,
                "Content-Type" : "application/x-www-form-urlencoded",
                "Upgrade-Insecure-Requests" : "1",
                "Origin" : "http://seasonvar.ru",
                "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:35.0) Gecko/20100101 Firefox/35.0"
                }                    
            values = {
                "login": login,
                "password": password
                }
        
            cj = cookielib.CookieJar()
            opener = build_opener(HTTPCookieProcessor(cj), HTTPHandler())
            req = Request(self.url + "/?mod=login", urllib.urlencode(values), headers)
            f = opener.open(req)
            
            for cookie in cj:
                cookie = str(cookie).split('svid=')[-1].split(' ')[0].strip()
                if cookie and (cookie > ""):
                    self.authcookie = "svid=" + cookie
                    self.vip = True

    def main(self):
        self.log("Addon: %s"  % self.id)
        self.log("Handle: %d" % self.handle)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)

        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None

        keyword = params['keyword'] if 'keyword' in params else None
        external = 'unified' if 'unified' in params else None
        if external == None:
            external = 'usearch' if 'usearch' in params else None    
        transpar = params['translit'] if 'translit' in params else None

        withMSeason = params['wm'] if 'wm' in params else "1"
        idPlaylist = int(params['idpl']) if 'idpl' in params else 0

        page = int(params['page']) if 'page' in params else None

        filterType = int(params['ft']) if 'ft' in params else None
        filterValue = params['fv'] if 'fv' in params else None
        alphaBeta = int(params['ab']) if 'ab' in params else 0   
        
        if mode == 'play':
            self.playItem(url)
        if mode == 'search':
            self.search(keyword, external, transpar)
        if mode == 'show':
            self.getFilmInfo(url, (withMSeason == "1"))
        if mode == 'filter':
            self.getFilter(filterType, filterValue, alphaBeta)
        if mode == 'nextdate':
            self.getItemsByDate(page)
        if mode == 'playlist':
            self.partPlaylist(url, idPlaylist)
        elif mode is None:
            self.mainMenu()

    def mainMenu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(2000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        uri = sys.argv[0] + '?mode=%s' % ("filter")
        item = xbmcgui.ListItem("[COLOR=FF7B68EE]%s[/COLOR]" % self.language(3000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.getItems()

        xbmc.executebuiltin('Container.SetViewMode(52)')
        xbmcplugin.endOfDirectory(self.handle, True)
        
    def getSerialImage(self, url):
        if (not self.load_thumbnails) or (self.load_thumbnails == "false"):
            return self.icon
        else:    
            response = common.fetchPage({"link": url})            
            image = response["content"].split('<link rel="image_src" href="')[-1].split('" />')[0]
            return image

    def getItemsByDate(self, page):
        if (not self.contentBegin) or (page == 0):
            data = self.getMainContent().split('<div class="msg msg-news">')[-1].split('</body>')[0]
            self.contentBegin = data
        else:
            data = self.contentBegin

        dateitems = common.parseDOM(data, "div", attrs={"class": "film-list-block"})
        count = len(dateitems)
        dateitemnext = None
        
        try:
            dateitem = dateitems[page]
        except:
            return

        filmitems = common.parseDOM(dateitem, "div", attrs={"class": "film-list-item"})
        for filmitem in filmitems:
            title = self.strip(common.parseDOM(filmitem, "a", attrs={"class": "film-list-item-link"})[0])
            title_ = title.split('(')[0].strip()
            title = title + ' ' + filmitem.split('</a>')[-1].split('<span>')[0].strip()
            title = title + ' [COLOR=FF00FFF0][' + common.parseDOM(filmitem, "span")[0] + '][/COLOR]'
            link = common.parseDOM(filmitem, "a", ret="href")[0]
            uri = sys.argv[0] + '?mode=show&url=%s&wm=0' % (self.url + link)
            image = self.getSerialImage(self.url + link)
            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            item.setInfo(type='Video', infoLabels={'title': title})
            commands = []
            uricmd = sys.argv[0] + '?mode=search&keyword=%s' % (title_)
            commands.append(('[COLOR=FFFFD700]' + self.language(2000) + '[/COLOR]', "Container.Update(%s)" % (uricmd), ))
            item.addContextMenuItems(commands)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            
        if page > 0:
            uri = sys.argv[0] + '?'
            item = xbmcgui.ListItem('[COLOR=FFFFD700]' + self.language(9001) + '[/COLOR]', thumbnailImage=self.inext, iconImage=self.inext)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            
        if (page + 1) < count:
            dateitemnext = dateitems[page+1]       
            date = common.parseDOM(dateitemnext, "div", attrs={"class": "ff1"})[0]            
            uri = sys.argv[0] + '?mode=%s&page=%s' % ("nextdate", str(int(page) + 1))
            item = xbmcgui.ListItem('[COLOR=FFFFD700]' + self.language(9000) % (date) + '[/COLOR]', thumbnailImage=self.inext, iconImage=self.inext)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmc.executebuiltin('Container.SetViewMode(52)')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getItems(self, page = 0):
        print "*** Get items"
        content = None

        if (self.begin_render_type == None) or (self.begin_render_type == 'new'):
            url_ = self.url + '/ajax.php?mode=new'
        elif (self.begin_render_type == 'popular'):
            url_ = self.url + '/ajax.php?mode=pop'
        elif (self.begin_render_type == 'newest'):
            url_ = self.url + '/ajax.php?mode=newest'
        elif (self.begin_render_type == 'bydate'):
            self.getItemsByDate(page)
            return
        else:
            url_ = self.url + '/ajax.php?mode=new'
            
        values = {}
        headers = {
            "Host" : "seasonvar.ru",
            "Connection" : "keep-alive",
            "X-Requested-With" : "XMLHttpRequest",
            "Referer" : url_,
            "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:35.0) Gecko/20100101 Firefox/35.0"
        }
        request = urllib2.Request(url_, urllib.urlencode(values), headers)
        content = urllib2.urlopen(request).read()            

        if content:
            items = common.parseDOM(content, "div", attrs={"class": "news-block"})
            for item in items:
                titlediv = common.parseDOM(item, "div", attrs={"class": "news-right"})
                title = common.parseDOM(titlediv, "b")[0]
                title_ = title.split('(')[0].strip()
                seasondiv = common.parseDOM(titlediv, "div", attrs={"style": "font-size: 10px;color: #fda901;font-weight: normal;"})
                if seasondiv:
                    title = title + ' (' + seasondiv[0].replace('<b>', '').replace('</b>', '') + ') '
                titleadd = common.parseDOM(titlediv, "div", attrs={"class": "news-right-add"})[0]
                title = self.strip(title + ' [COLOR=FF00FFF0][' + titleadd + '][/COLOR]')
                urldiv = common.parseDOM(item, "div", attrs={"class": "news-left"})
                image = common.parseDOM(urldiv, "img", ret="src")[0]
                link = common.parseDOM(urldiv, "a", ret="href")[0]
                uri = sys.argv[0] + '?mode=show&url=%s&wm=0' % (self.url + link)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title})

                commands = []
                uricmd = sys.argv[0] + '?mode=search&url=%s&keyword=%s' % (self.url, title_)                
                commands.append(('[COLOR=FFFFD700]' + self.language(2000) + '[/COLOR]', "Container.Update(%s)" % (uricmd), ))
                item.addContextMenuItems(commands)

                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            
            xbmc.executebuiltin('Container.SetViewMode(52)')
            xbmcplugin.endOfDirectory(self.handle, True)
            
    def getCookies(self):
        sc = ""
        if self.vip == True:
            sc = self.authcookie
            if self.quality == "sd":
                sc += "; hdq=1"
        return sc

    def getParamsForRequestPlayList(self, content):
        if self.vip == True:
            idseason = common.parseDOM(content, 'div', attrs={'class': 'pgs-sinfo'}, ret='data-id-season')[0]
            idserial = common.parseDOM(content, 'div', attrs={'class': 'pgs-sinfo'}, ret='data-id-serial')[0]
            div = common.parseDOM(content, 'div', attrs={'class': 'pgs-player'})[0]
            secure = div.split("'secureMark': '")[-1].split("',")[0]
        else:
            content_ = content.split('<div id="confirmHd">')[-1].split("</body>")[0]
            div = common.parseDOM(content_, 'script', attrs={'type': 'text/javascript'})[0]
            idseason = div.split('var id = "')[-1].split('";')[0]
            idserial = div.split('var serial_id = "')[-1].split('";')[0]
            secure = div.split('var secureMark = "')[-1].split('";')[0]
        return idseason, idserial, secure

    def getURLPlayListFromContent(self, content, kind):
        if self.vip == True:
            if (kind == 0):
                playlist = content.split('<script>var pl = {\'0\': "')[-1].split('"};</script>')[0]
            else:
                playlist = content.split('<script>pl[68] = "')[-1].split('";</script>')[0]
        else:
            if (kind == 0):            
                content_ = content.split('function hdOut()')[-1].split('</script>')[0]
                playlist = content_.split('var pl0 = "')[-1].split('";')[0]
            else:
                content_ = common.parseDOM(content, "div", attrs={"id": "translateDivParent"})[0]
                playlist = content_.split('var pl68 = "')[-1].split('";')[0]
        return self.url + playlist   
        
    def getURLPlayList(self, url, content, kind):

        idseason, idserial, secure = self.getParamsForRequestPlayList(content)
        
        headers = {
            "Cookie": self.getCookies(),
            "Host": "seasonvar.ru",
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

        request = urllib2.Request(self.url + "/player.php", urllib.urlencode(values), headers)
        content = urllib2.urlopen(request).read()            
        
        return self.getURLPlayListFromContent(content, kind)
        
    def partPlaylist(self, url, idPlaylist):
        response = common.fetchPage({"link": url, "cookie": self.getCookies()})
        image = common.parseDOM(response["content"], 'link', attrs={'rel': 'image_src'}, ret='href')[0] if common.parseDOM(response["content"], 'link', attrs={'rel': 'image_src'}, ret='href') else None
        description = common.parseDOM(response["content"], 'meta', attrs={'name': 'description'}, ret='content')[0] if common.parseDOM(response["content"], 'meta', attrs={'name': 'description'}, ret='content') else ''
        response = common.fetchPage({"link": self.getURLPlayList(url, response["content"], 0), "cookie": self.getCookies()})
        json_playlist = json.loads(response["content"])
        playlist = json_playlist['playlist']
        i = 0
        for episode in playlist:
            try:            
                playlist_ = episode['playlist']
            except:
                playlist_ = None
            if playlist_:
                if (i == idPlaylist):
                    self.parsePlaylist(url, playlist_, image, description)
                    break
                else:
                    i += 1                    
        xbmc.executebuiltin('Container.SetViewMode(503)')           
        xbmcplugin.endOfDirectory(self.handle, True)

    def parsePlaylist(self, url, playlist, image, description):
        for episode in playlist:
            etitle = self.strip(episode['comment'].replace("<br>", "  "))
            playlist_ = None
            try:
                url = episode['file']
            except:
                playlist_ = episode['playlist']
            if playlist_:
                self.addplaylists.append(playlist_)
                uri = sys.argv[0] + '?mode=playlist&url=%s&idpl=%d' % (url, (len(self.addplaylists)-1))
                item = xbmcgui.ListItem('[COLOR=FFFFD700]' + etitle + '[/COLOR]', iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': etitle})
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            else:    
                uri = sys.argv[0] + '?mode=play&url=%s' % url
                item = xbmcgui.ListItem(label=etitle, label2=description, iconImage=image, thumbnailImage=image)
                labels = {'title': description if description != '' else etitle, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0}
                item.setInfo(type='Video', infoLabels=labels)
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

    def getPlaylistByUppod(self, content):
        divplayer = common.parseDOM(content, 'div', attrs={'id': 'videoplayer719'})
        hashdiv = common.parseDOM(divplayer, "script", attrs={"type": "text/javascript"})[0]
        uhash = hashdiv.split('var pl0 = "')[-1].split('";')[0] if 'var pl0 = "' in hashdiv else None
        pl_url = Decoder.Decode_String(uhash, 'JpvnsR03Tmwu9xgaGLUXztb7H=' + '\n' + 'fNW5elVDyZIiMoQ1B826cd4YkC')
        response = common.fetchPage({"link": self.url + pl_url})
        json_playlist = json.loads(response["content"])
        playlist = json_playlist['playlist']
        if not playlist:
            hashdiv = common.parseDOM(divplayer, "div", attrs={"id": "translateDivParent"})[0]
            uhash = hashdiv.split('var pl68 = "')[-1].split('";')[0] if 'var pl68 = "' in hashdiv else None
            pl_url = Decoder.Decode_String(uhash, 'JpvnsR03Tmwu9xgaGLUXztb7H=' + '\n' + 'fNW5elVDyZIiMoQ1B826cd4YkC')                
            response = common.fetchPage({"link": self.url + pl_url})
            json_playlist = json.loads(response["content"])
            
    def checkAccessContent(self, content):
            bad = common.parseDOM(content, 'div', attrs={'class': 'sobadcat'})
            if not bad:
                bad = common.parseDOM(content, 'div', attrs={'class': 'svtabr_wrap_hdtest'})
            if bad:
                self.showErrorMessage(self.strip(bad[0]))
                return False
            else:    
                return True

    def getMultiseasonDiv(self, content):
        return common.parseDOM(content, 'div', attrs={'class': 'pgs-seaslist' if self.vip else 'svtabr_wrap show seasonlist'})

    def getFilmInfo(self, url, withMSeason = True):
        print "*** getFilmInfo for url %s " % url

        response = common.fetchPage({"link": url, "cookie": self.getCookies()})
        content = response["content"]
        image = common.parseDOM(content, 'link', attrs={'rel': 'image_src'}, ret='href')[0] if common.parseDOM(response["content"], 'link', attrs={'rel': 'image_src'}, ret='href') else None
        description = common.parseDOM(content, 'meta', attrs={'name': 'description'}, ret='content')[0] if common.parseDOM(response["content"], 'meta', attrs={'name': 'description'}, ret='content') else ''
        multiseason = self.getMultiseasonDiv(content)

        if withMSeason and multiseason:
            serialitems = common.parseDOM(multiseason, "h2")
            for serialitem in serialitems:
                url = self.url + common.parseDOM(serialitem, "a", ret="href")[0]
                title = common.parseDOM(serialitem, "a")[0]
                title = title.replace('<span>', '[COLOR=FF00FFF0][').replace('</span>', '][/COLOR]').replace('<small>', '[COLOR=FF00FFF0][').replace('</small>', '][/COLOR]')
                title = ' '.join(title.split()).strip()
                uri = sys.argv[0] + '?mode=show&url=%s&wm=0' % url
                item = xbmcgui.ListItem(self.strip(title), iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title})
                item.select(title.find('>>>') > -1)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
           
        else:
            if not self.checkAccessContent(response["content"]):
                return

            self.addplaylists = []
            response = common.fetchPage({"link": self.getURLPlayList(url, content, 0), "cookie": self.getCookies()})
            json_playlist = json.loads(response["content"])
            playlist = json_playlist['playlist']
            if not playlist:
                response = common.fetchPage({"link": self.getURLPlayList(url, content, 1), "cookie": self.getCookies()})
                json_playlist = json.loads(response["content"])
                playlist = json_playlist['playlist']

            self.parsePlaylist(url, playlist, image, description)

        if multiseason:
           xbmc.executebuiltin('Container.SetViewMode(52)')
        else:
           xbmc.executebuiltin('Container.SetViewMode(503)')           

        xbmcplugin.endOfDirectory(self.handle, True)

    def playItem(self, url):
        print "*** play url %s" % url
        item = xbmcgui.ListItem(path=url)
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

    def newSearchMethod(self, keyword, external, unified_search_results):
        url = self.url +  '/search?q=' + keyword
        response = common.fetchPage({"link": url})
        data =  response["content"].split('<div class="center-title">')[-1].split('</body>')[0]           
        searchitems = common.parseDOM(data, 'div', attrs={'class': 'searchResult'})
        for searchitem in searchitems:
            urldiv = common.parseDOM(searchitem, "div", attrs={"class": "searchPoster"})
            url = self.url + common.parseDOM(urldiv, "a", ret="href")[0]
            image = common.parseDOM(urldiv, "img", ret="src")[0]
            titlediv = common.parseDOM(searchitem, "div", attrs={"class": "searchContent"})
            title = common.parseDOM(titlediv, "a")[0]
            seasondiv = common.parseDOM(titlediv, "div", attrs={'class': 'searchSeason'})
            if seasondiv:
                title = title + ' [COLOR=FF00FFF0][' + seasondiv[0] + '][/COLOR]'                  
            
            if (external == 'unified'):
                self.log("Perform unified search and return results")
                unified_search_results.append({'title': title, 'url': url, 'image': image, 'plugin': self.id})
            else:
                uri = sys.argv[0] + '?mode=show&url=%s&wm=1' % url
                item = xbmcgui.ListItem(title, thumbnailImage=image)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

    def search(self, keyword, external, transpar = None):
        print "*** search for keyword %s " % keyword
        
        keyword_ = keyword if keyword else self.getUserInput()
        if keyword_: 
            keyword_ = self.USTranslit(keyword_, transpar) if (external == 'unified') else urllib.unquote_plus(keyword)
            keyword_ if isinstance(keyword_, unicode) else unicode(keyword_)
        else:
           return 
        
        unified_search_results = []
        
        if keyword_:
            if self.new_search_method and (self.new_search_method == "true"):
                self.newSearchMethod(keyword_, external, unified_search_results)
            else:
                url = self.url + '/autocomplete.php?query=' + keyword_       
                response = common.fetchPage({"link": url})
                count = 1
                s = json.loads(response["content"])
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
                            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if (external == 'unified'):
                UnifiedSearch().collect(unified_search_results)
            else: 
                xbmc.executebuiltin('Container.SetViewMode(50)')
                xbmcplugin.endOfDirectory(self.handle, True)

        else:
            self.menu()

    def getFilterPrefix(self, filterType):
        return FILTER_TYPES[1][filterType]

    def getFilterTypeList(self, filterType):
        if self.contentFilter:
            content = self.contentFilter
        else:
            content = self.getMainContent().split('<div class="content-top">')[-1].split('<script type="text/javascript">')[0]
            self.contentFilter = content
            
        kind = self.getFilterPrefix(filterType)
        
        filterdiv = common.parseDOM(content, "select", attrs={"class": kind})[0]
        filterlist = common.parseDOM(filterdiv, "option")
        filteridlist = common.parseDOM(filterdiv, "option", ret="value")
        for i, filteritem in enumerate(filterlist):        
            fv = filteridlist[i]
            fvn = filteritem

            uri = sys.argv[0] + '?mode=filter&ft=%d&fv=%s' % (filterType, fv)

            item = xbmcgui.ListItem(fvn, iconImage=self.icon, thumbnailImage=self.icon)
            item.setInfo(type='Video', infoLabels={'title': fvn})
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmc.executebuiltin('Container.SetViewMode(52)')
        xbmcplugin.endOfDirectory(self.handle, True)
        
    def getFilterToValues(self, filterType, filterValue):
        values = {}
	if filterValue != "all":
	        values["filter[" + FILTER_TYPES[2][filterType] + "][]"] = urllib.unquote_plus(filterValue)
        values["filter[rait]"] = "kp"                     
        return values

    def getFilterValueList(self, filterType, filterValue, alphaBeta = 0):
        values = self.getFilterToValues(filterType, filterValue)
        
        request = urllib2.Request(self.url + "/index.php", urllib.urlencode(values), self.headers)
        content = urllib2.urlopen(request).read()

        abitems = common.parseDOM(content, "div", attrs={"class": "alf-block"})
        for i, abitem in enumerate(abitems):
            ab = common.parseDOM(abitem, "span")[0]
            if i == alphaBeta:
                filmitems = common.parseDOM(abitem, "a", attrs={"class": "betterT alf-link"})
                filmlinks = common.parseDOM(abitem, "a", attrs={"class": "betterT alf-link"}, ret="href")
                for j, filmitem in enumerate(filmitems):
                    try:
                        titleadd = ' [COLOR=FFFF4000][' + common.parseDOM(filmitem, "img", ret="title")[0] + '][/COLOR]'
                    except:
                        titleadd = ""
                    title = self.strip(filmitem) + titleadd
                    uri = sys.argv[0] + '?mode=show&url=%s&wm=1' % (self.url + filmlinks[j])
                    image = self.getSerialImage(self.url + filmlinks[j])
                    item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                    item.setInfo(type='Video', infoLabels={'title': title})
                    if titleadd > "":
                        item.setProperty('IsAvailable', 'false')
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            else:
                uri = sys.argv[0] + '?mode=filter&ft=%d&fv=%s&ab=%s' % (filterType, filterValue, i)
                image = self.icon
                item = xbmcgui.ListItem('[COLOR=FFFFD700]' + ab + '[/COLOR]', iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': ab})
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmc.executebuiltin('Container.SetViewMode(52)')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getFilterList(self):
        for i, filtertype in enumerate(FILTER_TYPES[0]):
            uri = sys.argv[0] + '?mode=%s&ft=%d' % ("filter", FILTER_TYPES[0][i])
            item = xbmcgui.ListItem("%s" % self.language(4000 + FILTER_TYPES[0][i]), thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        xbmc.executebuiltin('Container.SetViewMode(52)')
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
            print "### %s: %s" % (self.id, message)

    def error(self, message):
        print "%s ERROR: %s" % (self.id, message)

    def showErrorMessage(self, msg):
        print msg
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))

    def strip(self, string):
        return common.stripTags(string)

    def encode(self, string):
        return string.decode('cp1251').encode('utf-8')

Seasonvar = Seasonvar()
Seasonvar.main()
