#!/usr/bin/python
# Writer (c) 2012-2017, MrStealth, dandy
# Rev. 1.1.0
# -*- coding: utf-8 -*-

import os
import urllib
import urllib2
import sys
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import re
import XbmcHelpers
common = XbmcHelpers

import Translit as translit
translit = translit.Translit()

from operator import itemgetter

from videohosts import host_manager

# My Favorites module
from MyFavorites import MyFavorites

import SearchHistory as history

# YouTube module
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

from pytube import YouTube
yt = YouTube()

class URLParser():
    def parse(self, string):
        links = re.findall(r'(?:http://|www.).*?["]', string)
        return list(set(self.filter(links)))

    def filter(self, links):
        links = self.strip(links)
        return [l for l in links if l.endswith('.mp4') or l.endswith('.mp4') or l.endswith('.txt')]

    def strip(self, links):
        return [l.replace('"', '') for l in links]

class OnlineLife():
    def __init__(self):
        self.id = 'plugin.video.online-life.cc'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString
        self.handle = int(sys.argv[1])
        self.domain = self.addon.getSetting('domain')
        self.url = 'http://' + self.addon.getSetting('domain')

        self.favorites = MyFavorites(self.id)

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.debug = False

    def main(self):
        params = common.getParameters(sys.argv[2])
        mode = url = page = None

        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        page = params['page'] if 'page' in params else 1

        keyword = params['keyword'] if 'keyword' in params else None
        external = 'main' if 'main' in params else None
        if not external:
            external = 'usearch' if 'usearch' in params else None

        if mode == 'play':
            self.play(url)
        if mode == 'search':
            self.search(keyword, external)
        if mode == 'history':
            self.history()
        if mode == 'genres':
            self.listGenres(url)
        if mode == 'show':
            self.getFilmInfo(url)
        if mode == 'category':
            self.getCategoryItems(url, page)
        if mode == 'favorites':
            self.show_favorites()
        elif mode is None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[B][COLOR=FF00FF00]%s[/COLOR][/B]" % self.language(2000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("history", self.url)
        item = xbmcgui.ListItem("[B][COLOR=FF00FF00]%s[/COLOR][/B]" % self.language(2003), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.favorites.ListItem()

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("genres", self.url)
        item = xbmcgui.ListItem("[B][COLOR=FF00FFF0]%s[/COLOR][/B]" % self.language(1000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("category",  self.url + "/kino-multserial/")
        item = xbmcgui.ListItem("[B][COLOR=FF00FFF0]%s[/COLOR][/B]" % self.language(1004), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.getCategoryItems(self.url + '/kino-new/', 1)

    def getCategoryItems(self, url, page):
        page_url = url if page == 0 else "%s/page/%s/" % (url, str(int(page)))
        response = common.fetchPage({"link": page_url})

        if response["status"] == 200:
            container = common.parseDOM(response["content"], "div", attrs={"id": "container"})
            posts = common.parseDOM(container, "div", attrs={"class": "custom-post media-grid"})
            extras = common.parseDOM(container, "div", attrs={"class": "extra"})
            pagenav = common.parseDOM(container, "div", attrs={"class": "navigation"})

            ratings = common.parseDOM(container, "li", attrs={"class": "current-rating"})
            items = 0

            for i, post in enumerate(posts):
                items += 1

                poster = common.parseDOM(post, "div", attrs={"class": "custom-poster"})
                media_data = common.parseDOM(extras[i], "div", attrs={"class": "media-data text-overflow"})

                title = self.encode(common.stripTags(common.parseDOM(poster, "a")[0]).split(']')[0] + ']')
                link = common.parseDOM(poster, "a", ret="href")[0]
                image = common.parseDOM(poster, "img", ret="src")[0]

                description = self.encode(common.stripTags(common.parseDOM(extras[i], "div", attrs={"class": "description"})[0]))
                genres = self.encode(', '.join(common.parseDOM(media_data, "a")))

                try:
                    rating = float(ratings[i]) / 10
                except IndexError:
                    rating = 0;

                uri = sys.argv[0] + '?mode=show&url=%s' % link
                item = xbmcgui.ListItem(title, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title, 'genre': genres, 'plot': description, 'rating': rating})

                self.favorites.addContextMenuItem(item, {'title': title, 'url': link, 'image': image, 'playable': False, 'action': 'add', 'plugin': self.id})

                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if pagenav and not items < 20:
                uri = sys.argv[0] + '?mode=%s&url=%s&page=%s' % ("category", url, str(int(page) + 1))
                item = xbmcgui.ListItem("[COLOR=orange]" + self.language(9001) + "[/COLOR]", thumbnailImage=self.inext)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        else:
            self.showErrorMessage("getCategoryItems(): Bad response status%s" % response["status"])

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getFilmInfo(self, url):
        response = common.fetchPage({"link": url})

        content = common.parseDOM(response["content"], "div", attrs={"id": "dle-content"})
        story = common.parseDOM(response["content"], "div", attrs={"class": "full-story"})

        title = self.encode(common.parseDOM(story, "span", attrs={"itemprop": "name"})[0])
        image = common.parseDOM(story, "img", attrs={"itemprop": "image"}, ret="src")[0]

        itemprop_genre = common.parseDOM(story, "span", attrs={"itemprop": "genre"})
        genres = self.encode(', '.join(common.parseDOM(itemprop_genre, 'a')))

        desc = self.encode(common.parseDOM(story, "div", attrs={"style": "display:inline;"})[0])

        manifest_links, subtitles, season, episode = host_manager.get_playlist(response["content"])

        if manifest_links:
             list = sorted(manifest_links.iteritems(), key=itemgetter(0))
             if season:
                title += " - s%se%s" % (season.zfill(2), episode.zfill(2)) 
             for quality, link in list:
                film_title = "[COLOR=lightgreen][%s][/COLOR] %s" % (str(quality), title)
                uri = sys.argv[0] + '?mode=play&url=%s&title=%s' % (urllib.quote_plus(link), title)
                item = xbmcgui.ListItem(film_title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': film_title, 'label': film_title, 'plot': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                item.setProperty('IsPlayable', 'true')
                if subtitles: 
                    item.setSubtitles([subtitles])
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
        else:
            self.showErrorMessage("Unknown host")
            return

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def add(self, url):
        link = self.getVideoSource(url)
        movie = link if not link.endswith('.txt') else None
        season = link if link.endswith('.txt') else None

        if movie:
            uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote_plus(movie)

            overlay = xbmcgui.ICON_OVERLAY_WATCHED
            item = xbmcgui.ListItem(title, thumbnailImage=image)

            info = {"Title": title, 'genre' : genres, "Plot": common.stripTags(desc), "overlay": overlay, "playCount": 0}
            item.setInfo( type='Video', infoLabels=info)
            item.setProperty('IsPlayable', 'true')

            xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
            xbmcplugin.setContent(self.handle, 'movies')

        elif season:
            print "This is a season %s" % season

            headers = {
                "Host": "play.cidwo.com",
                "Referer": "http://play.cidwo.com/player.php?newsid=" + self.getVideoID(url),
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
            }

            response = common.fetchPage({"link": season, "headers": headers})

            overlay = xbmcgui.ICON_OVERLAY_WATCHED

            if response["status"] == 200:
                response = eval(response["content"].replace('\t', '').replace('\r\n', ''))

                if 'playlist' in response['playlist'][0]:
                    print "This is a season multiple seasons"

                    for season in response['playlist']:
                        episods = season['playlist']

                        for episode in episods:
                            etitle = "%s (%s)" % (episode['comment'], common.stripTags(season['comment']))
                            url = episode['file']
                            uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote_plus(url)
                            item = xbmcgui.ListItem(etitle, thumbnailImage=image)

                            info = {"Title": title, 'genre' : 'genre', "Plot": desc, "overlay": overlay, "playCount": 0}
                            item.setInfo( type='Video', infoLabels=info)
                            item.setProperty('IsPlayable', 'true')
                            xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

                    xbmcplugin.setContent(self.handle, 'episodes')

                else:
                    print "This is one season"
                    for episode in response['playlist']:
                        etitle = episode['comment']
                        url = episode['file']

                        uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote_plus(url)
                        item = xbmcgui.ListItem(etitle, thumbnailImage=image)

                        overlay = xbmcgui.ICON_OVERLAY_WATCHED
                        info = {"Title": title, 'genre' : 'genre', "Plot": desc, "overlay": overlay, "playCount": 0}
                        item.setInfo( type='Video', infoLabels=info)
                        item.setProperty('IsPlayable', 'true')
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

                    xbmcplugin.setContent(self.handle, 'episodes')

    def getVideoID(self, url):
        return url.split('/')[-1].split('-')[0]

    def getVideoSource(self, url):
        id = self.getVideoID(url)

        url = "http://play.cidwo.com/js.php?id=%s" % id

        request = urllib2.Request(url)
        request.add_header('Referer', 'http://play.cidwo.com/player.php?newsid=' + id)
        request.add_header('Host', 'play.cidwo.com')

        response = urllib2.urlopen(request).read()

        return URLParser().parse(response)[0]

    def listGenres(self, url):
        response = common.fetchPage({"link": url})

        container = common.parseDOM(response["content"], "div", attrs={"class": "nav"})
        titles = common.parseDOM(container, "a", attrs={"class": "link1"})
        links = common.parseDOM(container, "a", attrs={"class": "link1"}, ret="href")


        cats = common.parseDOM(container, "li", attrs={"class": "pull-right nodrop"})


        titles += common.parseDOM(cats, "a")
        links += common.parseDOM(cats, "a", ret="href")

        uri = sys.argv[0] + '?mode=category&url=%s' % (self.url + "/kino-new/")
        item = xbmcgui.ListItem(self.language(1007), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        for i, title in enumerate(titles):
            link = links[i] if links[i].startswith('http') else self.url + links[i]
            uri = sys.argv[0] + '?mode=category&url=%s' % link
            item = xbmcgui.ListItem(self.encode(title), thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def show_favorites(self):
        self.favorites.list()
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def play(self, url):
        print "Play media URL: %s" % url

        hd = True if  self.addon.getSetting('hd_youtube_videos') == 'true' else False
        supported_resolutions = ['720p', '1080p'] if hd else ['360p', '480p']
        video_url = ''

        try:
            if 'youtube' in url:
                yt.url = url
                video_url = yt.videos[-1].url
            else:
                video_url = url

            print urllib.unquote(video_url)
            item = xbmcgui.ListItem(path=video_url)
            xbmcplugin.setResolvedUrl(self.handle, True, item)
        except Exception, e:
            self.showErrorMessage(e)

    def history(self):
        words = history.get_history()
        for word in reversed(words):
            uri = sys.argv[0] + '?mode=%s&keyword=%s&main=1' % ("search", word)
            item = xbmcgui.ListItem(word, iconImage=self.icon, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.endOfDirectory(self.handle, True)

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

            history.add_to_history(keyword)

        return keyword

    def search(self, keyword, external):
        self.log("*** Search")

        keyword = urllib.unquote_plus(keyword) if (external != None) else self.getUserInput()

        if keyword:
            url = self.url + '/?do=search'

            # Advanced search: titles only
            values = {
                "do": "search",
                "subaction": "search",
                "mode": "simple",  
                "story": keyword.encode("cp1251"),
                "x": "0",
                "y": "0" 
            }

            data = urllib.urlencode(values)
            request = urllib2.Request(url, data)
            response = urllib2.urlopen(request).read()

            container = common.parseDOM(response, "div", attrs={"id": "container"})
            posts = common.parseDOM(container, "div", attrs={"class": "custom-post"})

            if posts:
                for i, post in enumerate(posts):
                    poster = common.parseDOM(post, "div", attrs={"class": "custom-poster"})
                    title = self.encode(common.stripTags(common.parseDOM(post, "a")[0]))
                    link = common.parseDOM(post, "a", ret="href")[0]
                    image = common.parseDOM(post, "img", ret="src")[0]

                    uri = sys.argv[0] + '?mode=show&url=%s' % link
                    item = xbmcgui.ListItem(title, thumbnailImage=image)

                    self.favorites.addContextMenuItem(item, {
                        'title': title,
                        'url': link,
                        'image': image,
                        'playable': False,
                        'action': 'add',
                        'plugin': self.id
                    })

                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

                xbmcplugin.setContent(self.handle, 'movies')
            #else:
            #    if external != "usearch": 
            #        item = xbmcgui.ListItem(self.language(2001), iconImage=self.icon, thumbnailImage=self.icon)
            #        xbmcplugin.addDirectoryItem(self.handle, '', item, True)
            xbmcplugin.endOfDirectory(self.handle, True)
        else:
            self.menu()

    # Addon helpers
    def log(self, message):
        if self.debug:
            print "### %s: %s" % (self.id, message)

    def error(self, message):
        print "%s ERROR: %s" % (self.id, message)

    def isCyrillic(self, keyword):
        if not re.findall(u"[\u0400-\u0500]+", keyword):
            return False
        else:
            return True

    def showErrorMessage(self, msg):
        print msg
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))

    def encode(self, string):
        return string.decode('cp1251').encode('utf-8')

plugin = OnlineLife()
plugin.main()
