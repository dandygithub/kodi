#!/usr/bin/python
# -*- coding: utf-8 -*-
# Writer (c) 2018, dandy

import os, urllib, urllib2, sys
import xbmc, xbmcplugin,xbmcgui,xbmcaddon
import re
import json

import XbmcHelpers
common = XbmcHelpers

class Videokvadrat():
    def __init__(self):
        self.id = 'plugin.video.dandy.videokvadrat.com'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString
        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.handle = int(sys.argv[1])
        self.domain = self.addon.getSetting('domain')
        self.url = 'http://' + self.addon.getSetting('domain') + '/'

    def main(self):
        params = common.getParameters(sys.argv[2])
        
        mode = url = page = None
        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        page = params['page'] if 'page' in params else 1
        keyword = urllib.unquote_plus(params['keyword']) if 'keyword' in params else None

        if mode == None:
            self.menu()
        if mode == 'play':
            self.play(url)
        if mode == 'show':
            self.show(url)
        if mode == 'index':
            self.index(url, page)
        if mode == 'history':
            self.history()
        if mode == 'clean':
            self.clean()
        if (mode == 'search') or (mode == 'search_main'):
            self.search(url, keyword, mode == "search_main")

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search_main", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1000), iconImage=self.icon, thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s' % ("history")
        item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1001), iconImage=self.icon, thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", self.url + "news/")
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1003), iconImage=self.icon, thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
		
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", self.url + "publ/")
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1004), iconImage=self.icon, thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.index(self.url, 0)

        xbmcplugin.setContent(self.handle, "files")
        xbmcplugin.endOfDirectory(self.handle, True)

    def history(self):    
        uri = sys.argv[0] + '?mode=%s' % ("clean")
        item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1002), iconImage=self.icon, thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        
        words = []
        history = self.addon.getSetting('history')
        if history:
        	words = history.split(",")
        
        for word in reversed(words):
        	uri = sys.argv[0] + '?mode=%s&keyword=%s&url=%s' % ("search_main", word, self.url)
        	item = xbmcgui.ListItem(word, iconImage=self.icon, thumbnailImage=self.icon)
        	xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.endOfDirectory(self.handle, True)

    def clean(self):
        self.addon.setSetting('history', '')
      
    def index_(self, content):
        div = common.parseDOM(content, "div", attrs={"class": "row"})[0]
        titlesdiv = common.parseDOM(div, "div", attrs={"class": "title"})
        
        links = common.parseDOM(titlesdiv, "a", ret='href')
        titles = common.parseDOM(titlesdiv, "a")

        for i, title in enumerate(titles):
            uri = sys.argv[0] + '?mode=show&url=%s' % (links[i] if ("http" in links[i]) else (self.url + links[i]))
            item = xbmcgui.ListItem("%s" % (title), iconImage = self.icon, thumbnailImage = self.icon)
            item.setInfo(type='Video', infoLabels={'title': title})
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
      
    def index(self, url, page):
        if page == 1:
            uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", url)
            item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1000), iconImage=self.icon, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        page_url = "%s%s" % (url, "" if (page == 0) else '?page' + str(page))

        response = common.fetchPage({"link": page_url})
        content = response["content"]

        self.index_(content)

        if page > 0:
            uri = sys.argv[0] + '?mode=%s&url=%s&page=%s' % ("index", url, str(int(page) + 1))
            item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1005), iconImage=self.inext)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            xbmcplugin.setContent(self.handle, "movies")
            xbmcplugin.endOfDirectory(self.handle, True)

    def show(self, url):
        try:
            self.show_(url)
        except:
            self.showErrorMessage("Source not supported")

    def show__(self, content, i):
        #title = common.parseDOM(content, "title")[0]
        title = "Video #" + str(i)
    
	if 'youtube.com/embed' in content:
		videoId = re.findall('youtube.com/embed/(.*?)[\"\']', content)[0].split('?')[0]
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
	elif 'videomore' in content:
		videoId = re.findall('videomore.ru/embed/(.*?)[\"\']', content)[0].split('?')[0]
		link = urllib.quote_plus('https://player.videomore.ru/?partner_id=97&track_id=%s&autoplay=1&userToken=' % videoId)
	else:	
		player = common.parseDOM(content, "div", attrs={"class": "player"})[0]
		link = player.split("'video': [{'url': '")[-1].split("'}],")[0]
	
	return title, link

    def show_(self, url):
        response = common.fetchPage({"link": url})
	content = response["content"]
	
#	divtitle = common.parseDOM(content, "div", attrs={"class": "row"})[0]
#	title = common.parseDOM(divtitle, "h1")[0]
	
        videos = common.parseDOM(content, "iframe", ret="src") 
        if len(videos) == 0:
            videos.append(content)

        description = self.strip(common.parseDOM(content,  "div", attrs={"class": "alltext"}) [0].replace("<br>", " ").replace('"', ''))

        for i, video in enumerate(videos):
            title, link = self.show__(video + '"', i+1)
	
            uri = sys.argv[0] + '?mode=play&url=%s' % link
	    item = xbmcgui.ListItem(title, thumbnailImage=self.icon, iconImage=self.icon)
	    item.setInfo(type='Video', infoLabels={'title': title, 'plot': description, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
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
            keyword = kbd.getText()

        words = []
        history = self.addon.getSetting('history')
        if history:
        	words = history.split(",")
        if keyword and keyword not in words:
        	words.append(keyword)
        	self.addon.setSetting('history', ','.join(words))
        return keyword

    def search(self, url, keyword, main):
        if not keyword:
        	keyword = self.getUserInput()
        if keyword:
            if (main == True):
                self.search_(url, keyword, "publ/")
                self.search_(url, keyword, "news/")
            else:
                self.search_(url, keyword, "")

            xbmcplugin.setContent(self.handle, "movies")
            xbmcplugin.endOfDirectory(self.handle, True)

    def search_(self, url, keyword, sub):
        headers = {
            "Host": self.domain,
            "Origin": self.url,
            "Referer": url + sub,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
        }

        values = {
            "query": keyword,
            "a": "2" if ("publ" in (url + sub)) else "14"
        }

        request = urllib2.Request(url + sub, urllib.urlencode(values), headers)
        content = urllib2.urlopen(request).read()
          
        self.index_(content)

    def play(self, url):
        item = xbmcgui.ListItem(path = url)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    # XBMC helpers
    def showMessage(self, msg):
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("Info", msg, str(3 * 1000)))

    def showErrorMessage(self, msg):
        print msg
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(3 * 1000)))

    # Python helpers
    def encode(self, string):
        return string.decode('cp1251').encode('utf-8')

    def convert(s):
        try:
            return s.group(0).encode('latin1').decode('utf8')
        except:
            return s.group(0)

    def strip(self, string):
        return common.stripTags(string)

plugin = Videokvadrat()
plugin.main()
