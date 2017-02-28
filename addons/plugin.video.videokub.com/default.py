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
# Rev. 2.0.3.4

import os, urllib, urllib2, sys #, socket, cookielib, errno
import xbmc, xbmcplugin,xbmcgui,xbmcaddon
import re
import json

import XbmcHelpers
common = XbmcHelpers

import Translit as translit
translit = translit.Translit(encoding='cp1251')

# UnifiedSearch module
try:
    sys.path.append(os.path.dirname(__file__)+ '/../plugin.video.unified.search')
    from unified_search import UnifiedSearch
except: pass

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
        self.url = 'https://www.videokub.online/'

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
        if mode == 'history':
            self.history()
        if mode == 'clean':
            self.clean()
        if mode == 'search':
            self.search(keyword, unified, page)
        elif mode == None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1000), iconImage=self.icon, thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s' % ("history")
        item = xbmcgui.ListItem("[COLOR=FF00FF00][История поиска][/COLOR]" , iconImage=self.icon, thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
		
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("genres", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1003), iconImage=self.icon, thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.index('https://www.videokub.online/latest-updates/', 1)
        xbmcplugin.endOfDirectory(self.handle, True)

    def history(self):    
        uri = sys.argv[0] + '?mode=%s' % ("clean")
        item = xbmcgui.ListItem("[COLOR=FF00FF00][Очистить][/COLOR]", iconImage=self.icon, thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        
        words = []
        history = self.addon.getSetting('history')
        if history:
        	words = history.split(",")
        
        for word in reversed(words):
        	uri = sys.argv[0] + '?mode=%s&keyword=%s' % ("search", word)
        	item = xbmcgui.ListItem(word, iconImage=self.icon, thumbnailImage=self.icon)
        	xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        xbmcplugin.endOfDirectory(self.handle, True)

    def clean(self):
		self.addon.setSetting('history', '')
      
    def genres(self):

        url = 'https://www.videokub.online/categories/'
        response = common.fetchPage({"link": url})
        block_content = common.parseDOM(response["content"], "div", attrs={"class": "block_content"})

        titles = common.parseDOM(block_content, "a", attrs={"class": "hl"})
        links = common.parseDOM(block_content, "a", attrs={"class": "hl"}, ret='href')
        images = common.parseDOM(block_content, "img", attrs={"class": "thumb"}, ret='src')

        for i, title in enumerate(titles):
            if 'http' in links[i]:
                link = links[i]
            else:
                link = self.url + links[i]

            uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", link)
            item = xbmcgui.ListItem(title, iconImage=images[i], thumbnailImage=images[i])
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)


        xbmcplugin.endOfDirectory(self.handle, True)


    def index(self, url, page):
        page_url = "%s%s/" % (url, page)

        print "Get videos for page_url %s" % page_url
        xbmc.log("url=" + page_url)
        response = common.fetchPage({"link": page_url})
        
        xbmc.log("status=" + str(response['status']))
        links = common.parseDOM(response["content"], "a", attrs={"itemprop": "url"}, ret='href')
        titles = common.parseDOM(response["content"], "span", attrs={"class": "item-title"})
        images = common.parseDOM(response["content"], "img", attrs={"class": "thumb"}, ret='src')

        durations = common.parseDOM(response["content"], "span", attrs={"class": "item-time"})

        for i, title in enumerate(titles):
            duration = durations[i].split(':')[0]

            uri = sys.argv[0] + '?mode=show&url=%s' % links[i]
            item = xbmcgui.ListItem("%s [COLOR=55FFFFFF](%s)[/COLOR]" % (title, durations[i]), iconImage=images[i], thumbnailImage=images[i])
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
		title = common.parseDOM(response["content"], "title")[0]
		content = response["content"]
		if 'youtube.com/embed' in content:
			videoId = re.findall('youtube.com/embed/(.*?)[\"\']', content)[0]
			link = urllib.quote_plus('plugin://plugin.video.youtube/play/?video_id=' + videoId)
		elif '1tv.ru/embed/' in content:
			videoId = re.findall('1tv.ru/embed/(.*?)[\"\']', content)[0]
			player = videoId.split(':')[-1]
			if '11' in player:
				url = 'https://www.1tv.ru/video_materials.json?news_id='+videoId.split(':')[0]
			if '12' in player:
				url = 'https://www.1tv.ru/video_materials.json?video_id='+videoId.split(':')[0]
			if '15' in player:
				url = 'https://www.1tv.ru/video_materials.json?legacy_id='+videoId.split(':')[0]
			if '16' in player:
				url = 'https://www.1tv.ru/video_materials.json?collection_id='+videoId.split(':')[0]
			if '17' in player:
				url = 'https://www.1tv.ru/video_materials.json?sort=none&type=news&legacy_id='+videoId.split(':')[0]
			request = urllib2.Request(url)
			request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
			response = urllib2.urlopen(request)
			resp = response.read()
			jsonDict = json.loads(resp)
			link = urllib.quote_plus('http:'+jsonDict[0]['mbr'][0]['src'])
		elif 'player.stb.ua/embed' in content or 'player.ictv.ua/embed' in content:
			if 'player.ictv.ua/embed' in content:
				url = re.findall('(player.ictv.ua/embed/.*?)[\"\']', content)[0]
				url = 'http://'+url
			if 'player.stb.ua/embed' in content:
				url = re.findall('(player.stb.ua/embed/.*?)[\"\']', content)[0]
				url = 'http://'+url
			request = urllib2.Request(url)
			request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
			response = urllib2.urlopen(request)
			resp = response.read()
			link = urllib.quote_plus(common.parseDOM(resp, "source", attrs={"label": "mq"}, ret="src")[0])
		elif 'ovva.tv/video/embed' in content:
			url = re.findall('(ovva.tv/video/embed/.*?)[\"\']', content)[0]
			url = 'https://'+url
			request = urllib2.Request(url)
			request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
			response = urllib2.urlopen(request)
			resp = response.read()
			resp = re.findall("ovva\('(.*?)'", resp)[0]
			import base64
			resp = base64.b64decode(resp)
			jsonDict = json.loads(resp)
			link = jsonDict['url']
			response = urllib2.urlopen(link)
			resp = response.read()
			link = urllib.quote_plus(resp.split('=')[-1])
		elif 'player.vgtrk.com/iframe' in content:
			videoId = re.findall('player.vgtrk.com/iframe/video/id/(.*?)/', content)[0]
			url = 'http://player.vgtrk.com/iframe/datavideo/id/'+videoId+'/sid/russiatv'
			request = urllib2.Request(url)
			request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
			response = urllib2.urlopen(request)
			resp = response.read()
			jsonDict = json.loads(resp)
			link = urllib.quote_plus(jsonDict['data']['playlist']['medialist'][0]['sources']['m3u8']['auto'])
		elif 'tvc.ru/video/iframe' in content:
			videoId = re.findall('tvc.ru/video/iframe/id/(.*?)/', content)[0]
			url = 'http://www.tvc.ru/video/json/id/'+videoId
			request = urllib2.Request(url)
			request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
			response = urllib2.urlopen(request)
			resp = response.read()
			jsonDict = json.loads(resp)
			link = urllib.quote_plus('http:'+jsonDict['path']['quality'][0]['url'])
		elif 'rutube.ru/play/embed/' in content:
			videoId = re.findall('rutube.ru/play/embed/(.*?)[\"\']', content)[0]
			url = 'http://rutube.ru/api/play/options/'+videoId+'?format=json'
			request = urllib2.Request(url)
			request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
			response = urllib2.urlopen(request)
			resp = response.read()
			jsonDict = json.loads(resp)
			link = urllib.quote_plus(jsonDict['video_balancer']['m3u8'])
		elif 'ntv.ru/video/embed/' in content:
			url = re.findall('(ntv.ru/video/embed/.*?)[\"\']', content)[0]
			url = 'http://'+url
			request = urllib2.Request(url)
			request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
			response = urllib2.urlopen(request)
			resp = response.read()
			resp = re.findall("CDATA\[(.*?)\]", resp)
			for r in resp:
				if 'mp4' in r and '_lo' not in r and 'mobile' not in r:
					link = urllib.quote_plus('http://media.ntv.ru/vod'+r)
					break
		else:	
			player = common.parseDOM(response["content"], "div", attrs={"class": "player"})[0]
			link = player.split("'video': [{'url': '")[-1].split("'}],")[0]

		#search_string = title.split(' ')

		# 'http://www.videokub.me/search/?q=%s' % (search_string[0] + ' ' + search_string[1])

		uri = sys.argv[0] + '?mode=play&url=%s' % link
		item = xbmcgui.ListItem(title, thumbnailImage=self.icon, iconImage=self.icon)
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
        s = None

        if kbd.isConfirmed():
            s = kbd.getText()
            if self.addon.getSetting('translit') == 'true':
                try:
                	keyword = translit.rus(s)	
                except:pass
                try:
                	keyword = self.encode(keyword)	
                except:keyword = s      
            else:
                keyword = s
        words = []
        history = self.addon.getSetting('history')
        if history:
        	words = history.split(",")
        if keyword and keyword not in words:
        	words.append(keyword)
        	self.addon.setSetting('history', ','.join(words))
        return keyword

    def search(self, keyword, unified, page):
        print "*** Search: unified %s" % unified

        if not keyword:
        	keyword = self.getUserInput()
        
        if keyword:
            
            url = 'https://www.videokub.online/search/'+str(page)+'/?q=%s' % (keyword)
            request = urllib2.Request(url)
            request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
            response = urllib2.urlopen(request)
            resp = response.read()

            links = common.parseDOM(resp, "a", attrs={"itemprop": "url"}, ret='href')
            titles = common.parseDOM(resp, "span", attrs={"class": "item-title"})
            images = common.parseDOM(resp, "img", attrs={"class": "thumb"}, ret='src')

            durations = common.parseDOM(resp, "span", attrs={"class": "item-time"})
            
            pages = common.parseDOM(resp, "div", attrs={"class": "pagination navigation"})
            pages = common.parseDOM(pages, "div", attrs={"class": "block_content"})
            pages = common.parseDOM(pages, "a", ret='href')

            if unified:
                print "Perform unified search and return results"

                for i, title in enumerate(titles):
                    # title = self.encode(title)
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

                if int(page)<=len(pages):
                	uri = sys.argv[0] + '?mode=%s&keyword=%s&page=%s' % ("search", keyword, str(int(page)+1))
                	item = xbmcgui.ListItem("следующая страница...", iconImage=self.icon, thumbnailImage=self.icon)
                	xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

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
        print 'url to play '+url
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
