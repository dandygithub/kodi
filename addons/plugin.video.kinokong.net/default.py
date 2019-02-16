#!/usr/bin/python
# Writer (c) 2014-2017, MrStealth, dandy
# Rev. 1.2.0
# -*- coding: utf-8 -*-

import os
import urllib
import urllib2
import sys
import re
import socket
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import XbmcHelpers
common = XbmcHelpers


import Translit as translit
translit = translit.Translit()

socket.setdefaulttimeout(120)


# UnifiedSearch module
try:
    sys.path.append(os.path.dirname(__file__)+ '/../plugin.video.unified.search')
    from unified_search import UnifiedSearch
except:
    pass

class Kinokong():
    def __init__(self):
        self.id = 'plugin.video.kinokong.net'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString

        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.domain = self.addon.getSetting('domain')
        self.url = 'http://'  + self.domain

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.debug = False

    def main(self):
        self.log("Addon: %s"  % self.id)
        self.log("Handle: %d" % self.handle)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)

        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        page = params['page'] if 'page' in params else 1

        keyword = params['keyword'] if 'keyword' in params else None
        external = 'unified' if 'unified' in params else None
        if external == None:
            external = 'usearch' if 'usearch' in params else None    

        if mode == 'play':
            self.playItem(url)
        if mode == 'search':
            self.search(keyword, external)
        if mode == 'genres':
            self.listGenres(url)
        if mode == 'show':
            self.getFilmInfo(url)
        if mode == 'category':
            self.getCategoryItems(url, page)
        elif mode is None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(2000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("genres", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.getCategoryItems(self.url + '/film/novinki-2019', 1)

    def getCategoryItems(self, url, page):
        #print "*** Get category items %s" % url
        page_url = "%s/page/%s/" % (url, str(int(page)))
        response = common.fetchPage({"link": page_url})
        per_page = 0
        pagenav = None

        if response["status"] == 200:
            content = common.parseDOM(response["content"], "div", attrs={"id": "container"})
            items = common.parseDOM(content, "div", attrs={"class": "owl-item"})

            link_container = common.parseDOM(items, "div", attrs={"class": "main-sliders-title"})
            titles = common.parseDOM(link_container, "a")
            links = common.parseDOM(link_container, "a", ret="href")
            images = common.parseDOM(items, "img", ret="src")

            descs = common.parseDOM(items, "i")
            pagenav = common.parseDOM(content, "div", attrs={"class": "navigation"})

            for i, title in enumerate(titles):
                per_page += 1
                title = self.strip(self.encode(title))

                image = images[(i+1)*3-1] if 'http' in images[(i+1)*3-1] else self.url+images[(i+1)*3-1]

                genres_cont = common.parseDOM(items[i], "em")
                genres = common.parseDOM(genres_cont, "a")
                genre = self.encode(', '.join(genres))
                description = self.strip(self.encode(descs[i]))

                uri = sys.argv[0] + '?mode=show&url=%s' % (links[i])
		self.log("image: %s"  % image)
		self.log("uri: %s"  % uri)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title, 'genre': genre, 'plot': description})

                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        if pagenav and not per_page < 15:
            uri = sys.argv[0] + '?mode=%s&url=%s&page=%s' % ("category", url, str(int(page) + 1))
            item = xbmcgui.ListItem(self.language(9000), thumbnailImage=self.inext, iconImage=self.inext)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getFilmInfo(self, url):
        print "*** getFilmInfo for url %s " % url
        response = common.fetchPage({"link": url})

        container = common.parseDOM(response["content"], "div", attrs={"id": "container"})
        js_container = common.parseDOM(response["content"], "div", attrs={"class": "section"})
        source2 = common.parseDOM(response["content"], "div", attrs={"id": "players"})[0]
        try:
            source = common.parseDOM(js_container, "script", attrs={"type": "text/javascript"})[6]
        except:
            source = source2    

        title = self.encode(common.parseDOM(container, "h1")[0])
        image = common.parseDOM(container, "img", attrs={"id": "imgbigp"}, ret="src")[0]
        quality = common.parseDOM(container, "div", attrs={"class": "full-quality"})
    
        movie = source.split('file":"')[-1].split('"};')[0] if 'file":"' in source else None
        if (not movie):
            movie = source2.split('file:"')[-1].split('"')[0] if 'file:"' in source2 else None
    
        playlist = source.split(',pl:"')[-1].split('"};')[0] if ',pl:"' in source else None
        playlist = playlist.split('",')[0] if playlist and '",' in playlist else playlist

        labels = {
            'title': title,
            'genre': 'genres',
            'plot': 'description',
            'playCount': 0,
            'year': 1970,
            'rating' : 0
        }

        if not playlist:
            links = movie.replace(' or ', ',').split(',') if(',' or ' or ') in movie else [movie]
            image = image if 'http' in image else self.url+image
            format = quality[0] if quality else ''

            for i, link in enumerate(links):
                if ("]" in link):
                    link = link.split("]")[1]
            
                if '_720' in link:
		    quality = '720P'
                else:
                    quality = '480P'

                link_title = "%s [%s - %s]" % (title, quality, format)
                link_title = link_title.replace(self.language(5002).encode('utf-8'), '').replace('720 hd', '')

                uri = sys.argv[0] + '?mode=play&url=%s' % link
                item = xbmcgui.ListItem(link_title,  iconImage=image, thumbnailImage=image)

                item.setInfo(type='Video', infoLabels={})
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

            xbmcplugin.setContent(self.handle, 'files')

        else:
            headers = {
                "Host": self.domain,
                "Referer": url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
            }
            
            request = urllib2.Request(playlist, "", headers)
            request.get_method = lambda: 'GET'
            response = eval(urllib2.urlopen(request).read())

            if 'playlist' in response['playlist'][0]:
                print "This is a season multiple seasons"

                for season in response['playlist']:
                    episods = season['playlist']

                    for episode in episods:
                        etitle =  episode['comment'].replace('<br>', '  ')
                        url = episode['file'].split(',')[-1] if '_720' in episode['file'] else episode['file'].split(',')[0]
                        uri = sys.argv[0] + '?mode=play&url=%s' % url
                        item = xbmcgui.ListItem(etitle.replace('<br>', '  '), iconImage=image, thumbnailImage=image)

                        item.setInfo(type='Video', infoLabels=labels)
                        item.setProperty('IsPlayable', 'true')
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
            else:
                print "This is one season"
                for episode in response['playlist']:
                    try:
                        etitle = episode['comment']
                    except KeyError:
                        etitle = episode['commet']

                    url = episode['file'].split(',')[-1] if '_720' in episode['file'] else episode['file'].split(',')[0]
                    uri = sys.argv[0] + '?mode=play&url=%s' % url
                    item = xbmcgui.ListItem(etitle.replace('<br>', '  '), iconImage=image, thumbnailImage=image)

                    item.setInfo(type='Video', infoLabels=labels)
                    item.setProperty('IsPlayable', 'true')
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

            xbmcplugin.setContent(self.handle, 'episodes')

        xbmcplugin.endOfDirectory(self.handle, True)


    def listGenres(self, url):
        print "list genres"
        response = common.fetchPage({"link": url})
        menu = common.parseDOM(response["content"], "ul", attrs={"class": "reset top-menu"})
        genres = common.parseDOM(menu, "li")

        links = [
          self.url + '/film/',
          self.url + '/film/novinki-kinoo/',
          self.url + '/series/',
          self.url + '/cartoons/',
          self.url + '/animes/',
          self.url + '/documentary/'
        ]

        for i, genre in enumerate(genres[:-1]):
            title = common.parseDOM(genre, "a")[0]
            link = links[i]

            uri = sys.argv[0] + '?mode=category&url=%s' % links[i]
            item = xbmcgui.ListItem(self.encode(title), iconImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getPlaylist(self, url):
        print "getPlaylist"

    def playItem(self, url):
        print "*** play url %s" % url
        if ' or ' in url:
            link = url.split(' or ')[-1]
        else:
            link = url
        item = xbmcgui.ListItem(path=link)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

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

    def search(self, keyword, external):
        keyword = keyword if (external != None) else self.getUserInput()
        keyword = translit.rus(keyword) if (external == 'unified') else urllib.unquote_plus(keyword)
        unified_search_results = []

        if keyword:
            # Advanced search: titles only
            values = {
                "beforeafter":  "after",
                "catlist[]":    0,
                "do" :          "search",
                "full_search":  0,
                "replyless":    0,
                "replylimit":   0,
                "resorder":     "desc",
                "result_from":  1,
                "search_start": 1,
                "searchdate" :  0,
                "searchuser":   "",
                "showposts":    0,
                "sortby":       "date",
                "story" :       self.decode(keyword),
                "subaction":    "search",
                "titleonly":    0
            }

            headers = {
                "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:35.0) Gecko/20100101 Firefox/35.0"
            }

            # Find redirected URL
            redirection = urllib2.Request(self.url, None, headers)
            url = urllib2.urlopen(redirection).geturl()

            # Send request to server
            request = urllib2.Request(url, urllib.urlencode(values), headers)
            response = urllib2.urlopen(request).read()

            content = common.parseDOM(response, "div", attrs={"id": "container"})
            items = common.parseDOM(content, "div", attrs={"class": "item"})

            link_container = common.parseDOM(items, "div", attrs={"class": "main-sliders-title"})
            titles = common.parseDOM(link_container, "a")
            links = common.parseDOM(link_container, "a", ret="href")
            images = common.parseDOM(items, "img", ret="src")

            descs = common.parseDOM(items, "i")

            if (external == 'unified'):
                self.log("Perform unified search and return results")

                for i, title in enumerate(titles):
                    image = images[i] if 'http' in images[i] else self.url+images[i]
                    unified_search_results.append({'title':  self.encode(self.strip(title)), 'url': links[i], 'image': image, 'plugin': self.id})

                UnifiedSearch().collect(unified_search_results)

            else:
                for i, title in enumerate(titles):
                    uri = sys.argv[0] + '?mode=show&url=%s' % links[i]
                    image = images[i] if 'http' in images[i] else self.url+images[i]
                    item = xbmcgui.ListItem(self.encode(self.strip(title)), thumbnailImage=image)
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

                xbmcplugin.setContent(self.handle, 'movies')
                xbmcplugin.endOfDirectory(self.handle, True)
        else:
            self.menu()


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

    def decode(self, string):
        return string.decode('utf-8').encode('cp1251')

Kinokong = Kinokong()
Kinokong.main()
