#!/usr/bin/python
# -*- coding: utf-8 -*-
#/*
# *  Copyright (C) 2011 MrStealth
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# */
#
# Writer (c) 2014, MrStealth
# Rev. 1.0.5

import os, urllib, urllib2, sys #, socket, cookielib, errno
import xbmc, xbmcplugin,xbmcgui,xbmcaddon
import re

import XbmcHelpers
common = XbmcHelpers

import Translit as translit
translit = translit.Translit(encoding='cp1251')


class VideoKub():
    def __init__(self):
        self.id = 'plugin.video.videokub.com'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString
        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.handle = int(sys.argv[1])
        self.url = 'http://www.videokub.me/'

    def main(self):
        params = common.getParameters(sys.argv[2])
        mode = url = page = None

        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        page = params['page'] if 'page' in params else 1

        keyword = params['keyword'] if 'keyword' in params else None
        unified = params['unified'] if 'unified' in params else None

        if mode == 'play':
            self.play(url)
        if mode == 'show':
            self.show(url)
        if mode == 'index':
            self.index(url, page)
        if mode == 'genres':
            self.genres()
        if mode == 'search':
            self.search(keyword, unified)
        elif mode == None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("genres", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1003), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.index('http://www.videokub.me/latest-updates/', 1)
        xbmcplugin.endOfDirectory(self.handle, True)

    def genres(self):
        response = common.fetchPage({"link": self.url})
        genres = common.parseDOM(response["content"], "ul", attrs={"class": "main"})

        titles = common.parseDOM(genres, "a")[1:]
        links = common.parseDOM(genres, "a", ret='href')[1:]

        for i, title in enumerate(titles):
            if 'http' in links[i]:
                link = links[i]
            else:
                link = self.url + links[i]

            uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", link)
            item = xbmcgui.ListItem(title, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)


        xbmcplugin.endOfDirectory(self.handle, True)


    def index(self, url, page):
        page_url = "%s%s/" % (url, page)

        print "Get videos for page_url %s" % page_url
        response = common.fetchPage({"link": page_url})
        content = common.parseDOM(response["content"], "div", attrs={"class": "list_videos"})
        videos = common.parseDOM(content, "div", attrs={"class": "short"})

        links = common.parseDOM(videos, "a", attrs={"class": "kt_imgrc"}, ret='href')
        titles = common.parseDOM(videos, "a", attrs={"class": "kt_imgrc"}, ret='title')
        images = common.parseDOM(videos, "img", attrs={"class": "thumb"}, ret='src')

        durations = common.parseDOM(videos, "span", attrs={"class": "time"})

        for i, title in enumerate(titles):
            duration = durations[i].split(':')[0]

            uri = sys.argv[0] + '?mode=show&url=%s' % links[i]
            item = xbmcgui.ListItem("%s [COLOR=55FFFFFF](%s)[/COLOR]" % (title, durations[i]), iconImage=images[i])
            item.setInfo(type='Video', infoLabels={'title': title, 'genre': durations[i], 'duration': duration})
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s&page=%s' % ("index", url, str(int(page) + 1))
        item = xbmcgui.ListItem(self.language(1004), iconImage=self.inext)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmc.executebuiltin('Container.SetViewMode(52)')
        xbmcplugin.endOfDirectory(self.handle, True)

    def show(self, url):
        print "Get video %s" % url
        response = common.fetchPage({"link": url})
        content = response["content"]
        scripts = common.parseDOM(response["content"], "script", attrs={"type": "text/javascript"})
        title = common.parseDOM(response["content"], "div", attrs={"class": "title"})[0]
        urls = []

        for script in scripts:
            if 'mp4' in script:
                urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', script)

        link = urls[0]

        print "link %s" % link

        search_string = title.split(' ')

        # 'http://www.videokub.me/search/?q=%s' % (search_string[0] + ' ' + search_string[1])

        uri = sys.argv[0] + '?mode=play&url=%s' % link
        item = xbmcgui.ListItem(title, thumbnailImage=self.icon)
        item.setInfo(type='Video', infoLabels={'title': title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

        xbmcplugin.endOfDirectory(self.handle, True)

    def getUserInput(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(1000))
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            if self.addon.getSetting('translit') == 'true':
                keyword = translit.rus(kbd.getText())
            else:
                keyword = kbd.getText()
        return keyword

    def search(self, keyword, unified):
        print "*** Search: unified %s" % unified

        keyword = translit.rus(keyword) if unified else self.getUserInput()
        unified_search_results = []

        if keyword:
            keyword = self.encode(keyword)

            url = 'http://www.videokub.me/search/?q=%s' % (keyword)
            response = urllib2.urlopen(url)
            content = common.parseDOM(response.read(), "div", attrs={"class": "list_videos"})
            videos = common.parseDOM(content, "div", attrs={"class": "short"})

            links = common.parseDOM(videos, "a", attrs={"class": "kt_imgrc"}, ret='href')
            titles = common.parseDOM(videos, "a", attrs={"class": "kt_imgrc"}, ret='title')
            images = common.parseDOM(videos, "img", attrs={"class": "thumb"}, ret='src')

            durations = common.parseDOM(videos, "span", attrs={"class": "time"})

            if unified:
                print "Perform unified search and return results"

                for i, title in enumerate(titles):
                    title = self.encode(title)
                    unified_search_results.append({'title':  title, 'url': links[i], 'image': self.url + images[i], 'plugin': self.id})

                UnifiedSearch().collect(unified_search_results)

            else:
                for i, title in enumerate(titles):
                    duration = durations[i].split(':')[0]

                    uri = sys.argv[0] + '?mode=show&url=%s' % urllib.quote(links[i])
                    item = xbmcgui.ListItem("%s [COLOR=55FFFFFF](%s)[/COLOR]" % (title, durations[i]), iconImage=images[i])
                    item.setInfo(type='Video', infoLabels={'title': title, 'genre': durations[i], 'duration': duration})
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

                # TODO: Fix search pagination
                # http://www.videokub.me/search/2/?q=%D0%B1%D0%B0%D1%80%D0%B1%D0%BE%D1%81%D0%BA&search=%D0%9D%D0%B0%D0%B9%D1%82%D0%B8
                #uri = sys.argv[0] + '?mode=%s&url=%s' % ("show", url)
                #item = xbmcgui.ListItem(self.language(1004), iconImage=self.inext)
                #xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

                xbmc.executebuiltin('Container.SetViewMode(52)')
                xbmcplugin.endOfDirectory(self.handle, True)

        else:
            self.menu()



# <div class="wrapper">
#     <div class="left">
#         <div class="middle" id="wide_col">
#             <div class="full">
#             <div class="title">Барбоскины - 121 серия. Семейный секрет</div>
#             <div class="content">
#             <div class="item">АВТОР: <a href="http://www.videokub.me/members/39/">videokub</a></div>
#             <div class="item">
#             <a href="http://www.videokub.me/categories/multfilmy/" title="">Mультфильмы</a>                                                    </div>
#             <div class="item">ОПИСАНИЕ: У видео нет описания</div>


        # xbmcplugin.endOfDirectory(self.handle, True)

    def play(self, url):
        item = xbmcgui.ListItem(path = url)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    # XBMC helpers
    def showMessage(self, msg):
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("Info", msg, str(5 * 1000)))

    def showErrorMessage(self, msg):
        print msg
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))

    # Python helpers
    def encode(self, string):
        return string.decode('cp1251').encode('utf-8')

    def convert(s):
        try:
            return s.group(0).encode('latin1').decode('utf8')
        except:
            return s.group(0)

plugin = VideoKub()
plugin.main()
