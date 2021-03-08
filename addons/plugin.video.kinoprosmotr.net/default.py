#!/usr/bin/python
# Writer (c) 2012-2016, MrStealth, dandy
# -*- coding: utf-8 -*-

import os
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import sys
import json
import re
from operator import itemgetter
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import XbmcHelpers
common = XbmcHelpers

import Translit as translit
translit = translit.Translit()

from videohosts import host_manager

import SearchHistory as history

class Kinoprosmotr():
    def __init__(self):
        self.id = 'plugin.video.kinoprosmotr.net'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString

        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.domain = self.addon.getSetting('domain')
        self.url = 'https://' + self.addon.getSetting('domain')

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.debug = False

    def main(self):
        self.log("Addon: %s"  % self.id)
        self.log("Handle: %d" % self.handle)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)

        mode = params['mode'] if 'mode' in params else None
        url = urllib.parse.unquote_plus(params['url']) if 'url' in params else None
        url2 = urllib.parse.unquote_plus(params['url2']) if 'url2' in params else None
        page = params['page'] if 'page' in params else 1

        keyword = params['keyword'] if 'keyword' in params else None
        external = 'main' if 'main' in params else None
        if not external:
            external = 'usearch' if 'usearch' in params else None

        if mode == 'play':
            self.playItem(url, url2)
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
        elif mode is None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(2000))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("history", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(2002))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })        
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("genres", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1000))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })        
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("category",  self.url + "/serial/")
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1001))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })        
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("category", self.url + "/mult/")
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1002))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })        
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.getCategoryItems(self.url, 1)

    def getCategoryItems(self, url, page):
        print("*** Get category items %s" % url)
        page_url = "%s/page/%s/" % (url, str(int(page)))
        response = common.fetchPage({"link": page_url})
        items = 0

        if response["status"] == 200:
            content = common.parseDOM(response["content"].decode("cp1251"), "div", attrs={"id": "page_content"})
            movie = common.parseDOM(content, "div", attrs={"class": "movie_teaser clearfix"})

            header = common.parseDOM(movie, "h2")
            links = common.parseDOM(header, "a", ret="href")
            titles = common.parseDOM(header, "a")

            poster = common.parseDOM(movie, "li", attrs={"class": "movie_teaser_poster"})
            images = common.parseDOM(poster, "img", ret="src")

            teaser = common.parseDOM(movie, "div", attrs={"class": "teaser_info"})
            descs = common.parseDOM(teaser, "div", attrs={"class": "teaser_desc"})

            infos = common.parseDOM(teaser, "ul", attrs={"class": "teaser_ads"})
            details = common.parseDOM(teaser, "ul", attrs={"class": "teaser_file_details"})

            ratings = common.parseDOM(movie, "li", attrs={"class": "current-rating"})
            pagenav = common.parseDOM(response["content"].decode("cp1251"), "div", attrs={"id": "pagenav"})

            for i, title in enumerate(titles):
                items += 1
                info = common.parseDOM(infos[i], "li")
                detail = common.parseDOM(details[i], "li")

                image = images[i]
                genre = ', '.join(common.parseDOM(info[2], "a"))
                year = info[1].split('</span>')[-1]
                desc = common.stripTags(descs[i])
                try:
                    rating = float(ratings[i])
                except:
                    rating = 0    

                try:
                    tmp = year.split(' ')
                    year = tmp[0]
                    season = tmp[1]+tmp[2]
                    title = "%s %s %s [COLOR=lightgreen][%s][/COLOR]" % (title, season, year, detail[2].split('</span>')[-1])
                except IndexError:
                    title = "%s (%s) [COLOR=lightgreen][%s][/COLOR]" % (title, year, detail[2].split('</span>')[-1])

                uri = sys.argv[0] + '?mode=show&url=%s' % (links[i])
                item = xbmcgui.ListItem(title)
                item.setArt({ 'thumb': self.url + image, 'icon' : self.url + image })        
                item.setInfo(type='Video', infoLabels={'title': title, 'genre': genre, 'plot': desc, 'rating': rating})

                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        else:
            self.showErrorMessage("getCategoryItems(): Bad response status%s" % response["status"])

        if pagenav and not items < 10:
            uri = sys.argv[0] + '?mode=%s&url=%s&page=%s' % ("category", url, str(int(page) + 1))
            item = xbmcgui.ListItem("[COLOR=orange]" + self.language(2003) + "[/COLOR]")
            item.setArt({ 'thumb': self.inext, 'icon' : self.inext })        
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def select_season(self, data):
        tvshow = common.parseDOM(data, "select", attrs={"name": "season"})
        seasons = common.parseDOM(tvshow[0], "option")
        values = common.parseDOM(tvshow[0], "option", ret="value")
        if len(seasons) > 1:
            dialog = xbmcgui.Dialog()
            index_ = dialog.select("Select season", seasons)
            if int(index_) < 0:
                index_ = -1    
        else:
            index_ = 0    
        if index_ < 0:
            return "", ""
        else:
            return values[index_], str(int(seasons[index_].split(" ")[-1]))

    def select_episode(self, data, url, headers):
        sindex = None
        eindex = None
        season, sindex = self.select_season(data)

        if season == "":
            return ""

        values = {
            "season": sindex,
            "ref": self.domain
        }  
        encoded_kwargs = urllib.parse.urlencode(list(values.items()))
        argStr = "?%s" %(encoded_kwargs)
        try: 
            request = urllib.request.Request(url.split('?')[0] + argStr, dict(""), headers)
            request.get_method = lambda: 'GET'
            data = urllib.request.urlopen(request).read().decode("utf-8")
        except:
            return ""

        tvshow = common.parseDOM(data, "select", attrs={"name": "episode"})
        series = common.parseDOM(tvshow[0], "option")
        evalues = common.parseDOM(tvshow[0], "option", ret="value")

        if len(series) > 1:
            dialog = xbmcgui.Dialog()
            index_ = dialog.select("Select episode", series)
            if int(index_) < 0:
                index_ = -1    
        else:
            index_ = 0  
        if int(index_) < 0:            
            return ""        
        episode = evalues[int(index_)]
        eindex = str(int(index_) + 1)

        values = {
            "season": season,
            "e": episode,
            "ref": self.domain
        }  
        encoded_kwargs = urllib.parse.urlencode(list(values.items()))
        argStr = "?%s" %(encoded_kwargs)

        try: 
            request = urllib.request.Request(url + argStr, dict(""), headers)
            request.get_method = lambda: 'GET'
            return urllib.request.urlopen(request).read().decode("utf-8")
        except:
            return ""

    def getFilmInfo(self, url):
        print("*** getFilmInfo")

        response = common.fetchPage({"link": url})
        response_ = response
        url2 = url

        if response["status"] == 200:
            content = response["content"].decode("cp1251")
            movie = common.parseDOM(content, "div", attrs={"class": "full_movie"})
            values = common.parseDOM(movie, "param", ret="value")
            values = None
            links = []
            list_links = {}

            scripts = common.parseDOM(content, 'script')

            for script in scripts:
                if('.mp4' in script):
                    link2 = script.split('file:"')[-1].split('",')[0]
                    content2 = common.fetchPage({"link": link2})
                    links = links.append(content2["content"].decode("cp1251").split('"file":"')[-1].split('"}')[0])
                if('"pl":"' in script):
                    link2 = script.split('"pl":"')[-1].split('",')[0]
                    values = common.fetchPage({"link": link2})

            if not values and not links:
                vp = common.parseDOM(response['content'].decode("cp1251"), 'object', attrs={"id": "videoplayer1257"})
                if vp:
                    link2 = vp[0].split(';pl=')[-1].split('&')[0]
                    values = common.fetchPage({"link": link2})

            if not values and not links:
                iframe = None
                try:
                    iframe = common.parseDOM(movie, "iframe", ret="src")[0]
                except:
                    try:
                        iframe = common.parseDOM(movie, "script", ret="src")[0]                    
                        response = common.fetchPage({"link": iframe})
                        iframe = response['content'].decode("cp1251").split('"src", "')[-1].split('");')[0]
                    except: 
                        pass
                if iframe:
                    
                    ############################################################
                    manifest_links, subtitles, season, episode = host_manager.get_playlist(movie)
                    ############################################################
                    
                    if manifest_links:
                        list_links = sorted(iter(manifest_links.items()), key=itemgetter(0))
                        for quality, link in list_links:
                            links.append(link)
                    else:
	                    link=iframe
	                    #import urlparse
	                    #linkparse = urlparse.urlsplit(iframe)
	                    host = "km396z9t3.xyz"
	                    #iframe = urlparse.urlunsplit((linkparse.scheme, host, linkparse.path, '', ''))
	                    #link = iframe + '?ref=' + self.domain
	                    url2 = urllib.parse.quote_plus(link)
	                    headers = {
	                       'Host': host,
	                       'Referer': iframe,
	                       'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
	                    }
	                    #try:  
	                    request = urllib.request.Request(link, dict(""), headers)
	                    request.get_method = lambda: 'GET'
	                    response = urllib.request.urlopen(request)
	                    data = response.read().decode("cp1251")
	
	                    #iframe = common.parseDOM(data, "iframe", ret="src")[0]
	                    #request = urllib2.Request(iframe, "", headers)
	                    #request.get_method = lambda: 'GET'
	                    #data = urllib2.urlopen(request).read()
	
	                    #tvshow
	                    tvshow = common.parseDOM(data, "select", attrs={"name": "season"})
	                    
	                    if tvshow:
	                        data = self.select_episode(data, iframe, headers)
	                        if (data == ""):
	                           return False
	
	                    data = data.split('media: [')[-1].split('],')[0]
	                    data = data.split('},{')
	                    for item in data:
	                        url_ = "http:" + item.split("url: '")[-1].split("'")[0]
	                        links.append(url_)
	                    #except:
	                    #    self.showErrorMessage('No media source (YouTube, ...)')
	                    #    return False

            poster = common.parseDOM(movie, "div", attrs={"class": "full_movie_poster"})
            description = common.parseDOM(movie, "div", attrs={"class": "full_movie_desc"})
            details = common.parseDOM(movie, "ul", attrs={"class": "full_movie_details_data"})
            infos = common.parseDOM(details, "li")

            image = common.parseDOM(poster, "img", ret="src")[0]
            image = self.url+image

            year = infos[2].split('</span>')[-1].split("(")[0].strip()

            title = "%s (%s)" % (common.parseDOM(infos[0], "h1")[0], year)
            genres = (', ').join(common.parseDOM(infos[4], "a"))
            desc = common.stripTags(description[0].split('<br>')[-1])

            if links:
                self.log("This is a film")
                for i, link in enumerate(links):   
                    uri = sys.argv[0] + '?mode=play&url=%s&url2=%s' % (link,url2)
                    quality = i+1
                    if list_links:
                        quality, link = list_links[i]
                    title_ = "[COLOR=orange][#%d][/COLOR]  %s" % (quality, title)
                    item = xbmcgui.ListItem(title_)
                    item.setArt({ 'thumb': image, 'icon' : image })
                    item.setInfo(type='Video', infoLabels={'title': title_, 'genre': genres, 'plot': desc, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                    item.setProperty('IsPlayable', 'true')
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

                xbmcplugin.setContent(self.handle, 'movies')
            else:
                print("This is a season")

                response = response_

                if response["status"] == 200:
                    player = ""
                    try:
                        player = common.parseDOM(response["content"].decode("utf-8"), "object", attrs={"type": "application/x-shockwave-flash"})[0]
                    except:
                        pass
                    pl_url = player.split("pl=")[-1].split("&")[0]
                    response = common.fetchPage({"link": pl_url})

                    response = eval(response["content"].decode("utf-8"))

                    if 'playlist' in response['playlist'][0]:
                        print("This is a season multiple seasons")

                        for season in response['playlist']:
                            episods = season['playlist']

                            for episode in episods:
                                etitle = "%s (%s)" % (episode['comment'], common.stripTags(season['comment']))
                                uri = sys.argv[0] + '?mode=play&url=%s&url2=%s' % (episode['file'], url2)
                                item = xbmcgui.ListItem(etitle)
                                item.setArt({ 'thumb': image, 'icon' : image })
                                info = {
                                    'title': title,
                                    'genre': genres,
                                    'plot': desc,
                                    'overlay': xbmcgui.ICON_OVERLAY_WATCHED,
                                    'playCount': 0
                                }

                                item.setInfo(type='Video', infoLabels=info)
                                item.setProperty('IsPlayable', 'true')
                                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
                    else:
                        print("This is one season")
                        for episode in response['playlist']:
                            etitle = episode['comment']
                            url_ = episode['file']

                            uri = sys.argv[0] + '?mode=play&url=%s&url2=%s' % (url_,url2)
                            item = xbmcgui.ListItem(etitle)
                            item.setArt({ 'thumb': image, 'icon' : image })
                            info = {
                                'title': title,
                                'genre': genres,
                                'plot': desc,
                                'overlay': xbmcgui.ICON_OVERLAY_WATCHED,
                                'playCount': 0
                            }

                            item.setInfo(type='Video', infoLabels=info)
                            item.setProperty('IsPlayable', 'true')
                            xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
                else:
                    self.showErrorMessage("getFilmInfo(): Bad response status%s" % response["status"])

                xbmcplugin.setContent(self.handle, 'episodes')

        else:
            self.showErrorMessage("getFilmInfo(): Bad response status%s" % response["status"])

        xbmcplugin.endOfDirectory(self.handle, True)

    def listGenres(self, url):
        print("list genres")
        response = common.fetchPage({"link": url})
        genres = common.parseDOM(response["content"].decode("cp1251"), "div", attrs={"class": "genres"})

        titles = common.parseDOM(genres, "a")
        links = common.parseDOM(genres, "a", ret="href")

        for i, title in enumerate(titles):
            uri = sys.argv[0] + '?mode=category&url=%s' % self.url + links[i]
            item = xbmcgui.ListItem(title)
            item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def playItem(self, url, url2):
        print("*** play url %s" % url)
        item = xbmcgui.ListItem(path=url + "|Referer="+url2)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def history(self):
        words = history.get_history()
        for word in reversed(words):
            uri = sys.argv[0] + '?mode=%s&keyword=%s&main=1' % ("search", word)
            item = xbmcgui.ListItem(word)
            item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
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
        keyword = urllib.parse.unquote_plus(keyword) if (external != None) else self.getUserInput()

        if keyword:
            #url =  self.url + '/index.php?do=search'
            url =  self.url

            # Advanced search: titles only
            values = {
                "beforeafter": "after",
                "catlist[]": 0,
                "do": "search",
                "full_search": "1",
                "replyless": "0",
                "replylimit": "0",
                "resorder": "desc",
                "result_from": "1",
                "result_num": "50",
                "search_start": "1",
                "searchdate": "0",
                "searchuser": "",
                "showposts": "0",
                "sortby": "date",
                "story": keyword.encode("cp1251"),
                "subaction": "search",
                "titleonly": "3"
            }

            headers = {
                "Referer" : self.url,
                "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0"
            }

            data = urllib.parse.urlencode(values).encode("utf-8")
            request = urllib.request.Request(url, data, headers)
            response = urllib.request.urlopen(request)

            containers = common.parseDOM(response.read().decode("cp1251"), "div", attrs={"class": "search_item clearfix"})
            search_item_prev = common.parseDOM(containers, "div", attrs={"class": "search_item_prev"})
            search_item_inner = common.parseDOM(containers, "div", attrs={"class": "search_item_inner"})

            descriptions = common.parseDOM(search_item_inner, "div")

            header = common.parseDOM(search_item_inner, "h3")
            gcont = common.parseDOM(search_item_inner, "span")

            titles = common.parseDOM(header, "a")
            links = common.parseDOM(header, "a", ret="href")
            images = common.parseDOM(search_item_prev, "img", ret="src")

            for i, title in enumerate(titles):
                image = self.url + images[i]
                genres = ', '.join(common.parseDOM(gcont[i], "a"))
                desc = common.stripTags(descriptions[i])
                uri = sys.argv[0] + '?mode=show&url=%s' % links[i]
                item = xbmcgui.ListItem(title)
                item.setArt({ 'thumb': image, 'icon' : image })
                item.setInfo(type='Video', infoLabels={'title': title, 'genre': genres, 'plot': desc})

                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            xbmcplugin.setContent(self.handle, 'movies')
            xbmcplugin.endOfDirectory(self.handle, True)
        else:
            self.menu()

    # *** Add-on helpers
    def log(self, message):
        if self.debug:
            print("### %s: %s" % (self.id, message))

    def error(self, message):
        print("%s ERROR: %s" % (self.id, message))

    def showErrorMessage(self, msg):
        print(msg)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))

    def encode(self, string):
        return string.encode('utf-8')

    def decode(self, string):
        return string.decode('utf-8')

class URLParser():
    def parse(self, string):
        links = re.findall(r'(?:http://|www.).*?["]', string)
        return list(set(self.filter(links)))

    def filter(self, links):
        links = self.strip(links)
        return [l for l in links if l.endswith('.mp4') or l.endswith('.mp4') or l.endswith('.txt')]

    def strip(self, links):
        return [l.replace('"', '') for l in links]

kinoprosmotr = Kinoprosmotr()
kinoprosmotr.main()
