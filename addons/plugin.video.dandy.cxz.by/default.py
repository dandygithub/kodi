# Writer (c) 2017, dandy
# Rev. 1.0.0
# -*- coding: utf-8 -*-

import os
import urllib
import urllib2
import sys
import re
import socket
import json
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
from operator import itemgetter
import XbmcHelpers
common = XbmcHelpers
from videohosts import moonwalk

socket.setdefaulttimeout(120)

ITEMS_PER_PAGE = 20
QUALITY_TYPES = (360, 480, 720, 1080)

class PopcornBY():
    def __init__(self):
        self.id = 'plugin.video.dandy.cxz.by'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString

        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.url = 'http://cxz.by'

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.debug = False

    def main(self):
        self.log("Addon: %s"  % self.id)
        self.log("Handle: %d" % self.handle)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)

        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        url2 = urllib.unquote_plus(params['url2']) if 'url2' in params else None
        id_kp = params['id_kp'] if 'id_kp' in params else None
        title = urllib.unquote_plus(params['title']) if 'title' in params else None
        season = params['season'] if 'season' in params else None
        image = urllib.unquote_plus(params['image']) if 'image' in params else None
        page = int(params['page']) if 'page' in params else 1
        pid = params['pid'] if 'pid' in params else None
        play = params['play'] if 'play' in params else None

        keyword = params['keyword'] if 'keyword' in params else None

        if mode == 'kino':
            self.menu_kino()
        if mode == 'tv':
            self.menu_tv()
        if mode == 'play':
            self.play_item(url, pid)
        if mode == 'search':
            self.search(keyword)
        if mode == 'searchcategory':
            self.search_category(url)
        if mode == 'show':
            self.show(url, id_kp, title, play)
        if mode == 'items':
            self.items(url, page)
        if mode == 'year':
            self.year()
        if mode == 'serial':
            self.serial(url, season, image, id_kp)
        elif mode is None:
            self.menu()

    def menu(self):
        self.menu_kino()
        return

        uri = sys.argv[0] + '?mode=kino&url=%s'%(self.url + '/online.php')
        item = xbmcgui.ListItem("[COLOR=FFFFD700]%s[/COLOR]" % self.language(1000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=tv' 
        item = xbmcgui.ListItem("[COLOR=FFFFD700]%s[/COLOR]" % self.language(1001), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def menu_kino(self):
        uri = sys.argv[0] + '?mode=search'
        item = xbmcgui.ListItem("[B][COLOR=FF00FF00]%s[/COLOR][/B]" % self.language(2000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=items&url=%s' % (self.url + "/stream/?yare=0000") 
        item = xbmcgui.ListItem("[COLOR=FFFFD700]%s[/COLOR]" % self.language(3000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=items&url=%s' % (self.url + "/stream/?yare=0001") 
        item = xbmcgui.ListItem("[COLOR=FFFFD700]%s[/COLOR]" % self.language(3001), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=items&url=%s' % (self.url + "/stream/?yare=") 
        item = xbmcgui.ListItem("[COLOR=FFFFD700]%s[/COLOR]" % self.language(3002), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=year' 
        item = xbmcgui.ListItem("[COLOR=FFFFD700]%s[/COLOR]" % self.language(3003), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)


    def menu_tv(self):
        response = common.fetchPage({"link": self.url})
        if response["status"] == 200:
            content = common.parseDOM(response["content"], "ul", attrs={"class": "dropdown-menu"})[0]
            items = common.parseDOM(content, "li")
            links = common.parseDOM(items, "a", ret="href")
            for i, item in enumerate(items):
                uri = sys.argv[0] + '?mode=tvsrc&url=%s' % (self.url + "/" +links[i])
                item = xbmcgui.ListItem(self.strip(item), iconImage=self.icon, thumbnailImage=self.icon)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)


    def serial_1(self, url, season, image, id_kp):
        headers = {
            "Referer": url
        }
        values = {
            "season": season,
            "episode": "1",
            "nocontrols_translations": ""
        }  

        request = urllib2.Request(url, urllib.urlencode(values), headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        serial = common.parseDOM(response, "select", attrs={"name": "episode"})
        series = common.parseDOM(serial[0], "option")
        for i, seria in enumerate(series):
            title = seria
            values = {
                "season": season,
                "episode": str(i+1),
                "nocontrols_translations": ""
            }  
            encoded_kwargs = urllib.urlencode(values.items())
            argStr = "?%s" %(encoded_kwargs)
            url_ = urllib.quote_plus(url + argStr)
            uri = sys.argv[0] + '?mode=show&url=%s&id_kp=%s&title=%s&play=1' % (url_, id_kp, title)
            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            item.setInfo(type='Video', infoLabels={"title": title})
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'tvshows')
        xbmcplugin.endOfDirectory(self.handle, True)

    def serial_2(self, url, season, image, id_kp):
        response = common.fetchPage({"link": url})
        if response["status"] != 200:
            return
        serial = common.parseDOM(response["content"], "div", attrs={"class": "serial-panel"})
        seriesbox = common.parseDOM(serial[0], "div", attrs={"class": "season-" + season})[0]
        series = common.parseDOM(seriesbox, "option")
        urls = common.parseDOM(seriesbox, "option", ret="value")
        for i, seria in enumerate(series):
            title = self.encode(seria)
            uri = sys.argv[0] + '?mode=show&url=%s&id_kp=%s&title=%s' % (urls[i], id_kp, title)
            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            item.setInfo(type='Video', infoLabels={"title": title})
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)


    def serial(self, url, season, image, id_kp):
        print "*** Get series list"
        if "moonwalk" in url:
            self.serial_1(url, season, image, id_kp)
        else:
            self.serial_2(url, season, image, id_kp)


    def year(self):
        print "*** Get years list"
        response = common.fetchPage({"link": self.url + "/online.php"})

        if response["status"] == 200:
            content = response["content"]

            itemsdiv = common.parseDOM(content, "select", attrs={"id": "my_select"})[0]
            years = common.parseDOM(itemsdiv, "option")

            for i, year_ in enumerate(years):
                try:
                    yeari = int(year_)
                except:
                    continue
                uri = sys.argv[0] + '?mode=items&url=%s' % (self.url + "/stream/?yare=" + year_)
                item = xbmcgui.ListItem("[COLOR=FFFFD700]%s[/COLOR]" % year_, iconImage=self.icon, thumbnailImage=self.icon)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def decorate_title(self, title):
        part1 = title.split("(")[0].strip()
        part2 = title.split("(")[-1].split(")")[0].strip()
        parts = title.split(")")[-1].strip()
        part3 = ""
        for i, parti in enumerate(parts.split(" ")):
            part3 = part3 + parti + (", " if (i < len(parts.split(" "))-1) else "")
        part2 = part2 + (", " if (part3 != "") else "")
        return "%s [COLOR=55FFFFFF][%s%s][/COLOR]" % (part1, part2, part3)

    def items(self, url, page):
        print "*** Get items %s" % url
        if (page == 0):
            page += 1;  

        response = common.fetchPage({"link": url})

        if response["status"] == 200:
            content = response["content"]
            items = common.parseDOM(content, "li")

            if (page == 1):
                uri = sys.argv[0] + '?mode=searchcategory&url=%s' % (url)
                item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(2000), thumbnailImage=self.icon)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            for i in range((page-1)*ITEMS_PER_PAGE if page == 1 else (page-1)*ITEMS_PER_PAGE-1, page*ITEMS_PER_PAGE):
                if i <= (len(items) - 1):
                    title = self.decorate_title(self.strip(items[i]))
                    links = common.parseDOM(items[i], "a", ret="href")
                    id_kp = items[i].split('onclick="id_kp(')[-1].split(');"')[0]
                    image = "http://st.kp.yandex.net/images/film/%s.jpg" % (id_kp) if id_kp else self.icon
                    uri = sys.argv[0] + '?mode=show&url=%s&url2=%s&id_kp=%s&title=%s' % (links[0], (links[1] if (len(links) > 1) else ""),  id_kp, title)
                    item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if page > 1:
                uri = sys.argv[0] + '?mode=items&url=%s&page=%d' % (url, 0)
                item = xbmcgui.ListItem("[COLOR=FFFFD700]%s[/COLOR]" % self.language(4001), thumbnailImage=self.inext, iconImage=self.inext)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if page*ITEMS_PER_PAGE < len(items):
                uri = sys.argv[0] + '?mode=items&url=%s&page=%d' % (url, page + 1)
                item = xbmcgui.ListItem(("[COLOR=FFFFD700]%s[/COLOR]" % self.language(4000)) % (page+1, len(items)//ITEMS_PER_PAGE + 1), thumbnailImage=self.inext, iconImage=self.inext)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)


    def select_translator(self, content, url):
        try:
            tr_div = common.parseDOM(content, 'select', attrs={"name": "translator"})[0]
        except:
            return content, url

        translators = common.parseDOM(tr_div, 'option')
        tr_values = common.parseDOM(tr_div, 'option', ret="value")

        if len(translators) > 1:
            dialog = xbmcgui.Dialog()
            index_ = dialog.select(self.language(1006), translators)
            if int(index_) < 0:
                index_ = 0    
        else:
            index_ = 0    
        tr_value = tr_values[index_]

        headers = {
            "Host": "moonwalk.cc",
            "Referer": url,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
        }

        url_ =  url.replace(url.split("serial/")[-1].split("/iframe")[0], tr_value)

        request = urllib2.Request(url_, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
        return response, url_


    def get_media_info(self, id_kp, title_):
        image = "http://st.kp.yandex.net/images/film/%s.jpg" % (id_kp)
        response = common.fetchPage({"link": "http://cxz.by/getmovie.php?kp_id=%s" % (id_kp)})
        if response["status"] != 200:
            return

        title = title_
        description = ""
        genre = ""
        links = [] 

        content = response["content"]
        if "h4" in content:
            titlefull = common.parseDOM(content, "h4")[0]
            title = titlefull.split("<br>")[0]
            genre = common.parseDOM(titlefull, "small")[0]
            description = content.split("</h4>")[-1].split("<br")[0]
            links = common.parseDOM(content, "a", ret="href")

        return image, title, genre, description


    def parse_by_moonwalk(self, url, image, id_kp, title, genre, description, play = None):
        playlist_domain = "moonwalk.cc"
        manifest_links = {}
        subtitles = None

        if (not play):
            headers = {
                "Host": "moonwalk.pw",
                "Referer": "http://cxz.by/online.php",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
            }
            try: 
                request = urllib2.Request(url, "", headers)
                request.get_method = lambda: 'GET'
                response = urllib2.urlopen(request).read()
            except:
                self.showErrorMessage("Content unavailable")
                return manifest_links, subtitles

            url_ = common.parseDOM(response, "iframe", ret="src")[0]
        else:
            url_ = url

        headers = {
            "Host": "moonwalk.cc",
            "Referer": url,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
        }

        try: 
            request = urllib2.Request(url_, "", headers)
            request.get_method = lambda: 'GET'
            response = urllib2.urlopen(request).read()
        except:
            self.showErrorMessage("Content unavailable")
            return manifest_links, subtitles

        #serial
        serial = common.parseDOM(response, "select", attrs={"name": "season"})
        if (not play) and serial:

            response, url_ = self.select_translator(response, url_)
            serial = common.parseDOM(response, "select", attrs={"name": "season"})

            seasons = common.parseDOM(serial[0], "option")
            values = common.parseDOM(serial[0], "option", ret="value")
            for i, season in enumerate(seasons):
                title = season
                uri = sys.argv[0] + '?mode=serial&url=%s&season=%s&image=%s&id_kp=%s' % (url_, values[i], image, id_kp)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={"title": title, "genre": genre, "plot": description})
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            xbmcplugin.setContent(self.handle, 'tvshows')
            xbmcplugin.endOfDirectory(self.handle, True)

            return manifest_links, subtitles

        if "var subtitles = JSON.stringify(" in response:
            subtitles = response.split("var subtitles = JSON.stringify(")[-1].split(");")[0]

        ###################################################
        values, attrs = moonwalk.get_access_attrs(response)
        ###################################################

        headers = {
            "Host": playlist_domain,
            "Origin": "http://" + playlist_domain,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            "Referer": url,
            "X-Requested-With": "XMLHttpRequest",
            "X-Frame-Commit": attrs['X-Frame-Commit']
        }
        request = urllib2.Request('http://' + playlist_domain + attrs['purl'], urllib.urlencode(values), headers)
        response = urllib2.urlopen(request).read()

        data = json.loads(response.decode('unicode-escape'))
        playlisturl = data['mans']['manifest_m3u8']

        headers = {
            "Host": "streamblast.cc",
            "Origin": "http://moonwalk.cc",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
        }
        request = urllib2.Request(playlisturl, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        urls = re.compile("http:\/\/.*?\n").findall(response)
        for i, url in enumerate(urls):
            manifest_links[QUALITY_TYPES[i]] = url.replace("\n", "")

        return manifest_links, subtitles


    def parse_alt(self, data, urlm):
        manifest_links = {}
        subtitles = None

        playerbox = common.parseDOM(data, "div", attrs={"class": "player_box"})[0]
        url = common.parseDOM(playerbox, "iframe", ret="src")[0]
        playlist_domain = url.split("http://")[-1].split("/")[0]

        headers = {
            "Referer": urlm,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
        }
        request = urllib2.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        ###################################################
        values, attrs = moonwalk.get_access_attrs(response)
        ###################################################

        headers = {
            "Host": playlist_domain,
            "Origin": "http://" + playlist_domain,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            "Referer": url,
            "X-Requested-With": "XMLHttpRequest",
            "X-Frame-Commit": attrs['X-Frame-Commit']
        }
        request = urllib2.Request('http://' + playlist_domain + attrs['purl'], urllib.urlencode(values), headers)
        response = urllib2.urlopen(request).read()

        data = json.loads(response.decode('unicode-escape'))
        playlisturl = data['mans']['manifest_m3u8']

        headers = {
            "Host": "streamblast.cc",
            "Origin": "http://video.kodik.name",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
        }
        request = urllib2.Request(playlisturl, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        urls = re.compile("http:\/\/.*?\n").findall(response)
        for i, url in enumerate(urls):
            manifest_links[QUALITY_TYPES[i]] = url.replace("\n", "")

        return manifest_links, subtitles


    def show_1(self, url, id_kp, title, image, genre, description, play):
        manifest_links, subtitles = self.parse_by_moonwalk(url, image, id_kp, title, genre, description, play)
        if manifest_links:
            list = sorted(manifest_links.iteritems(), key=itemgetter(0))
            for quality, link in list:
                film_title = "%s [COLOR=FF00FF00][%s][/COLOR]" % (title, str(quality) + '')
                uri = sys.argv[0] + '?mode=play&url=%s&pid=1' % urllib.quote(link)
                item = xbmcgui.ListItem(film_title, iconImage=image)
                item.setInfo(type='Video', infoLabels={'title': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                item.setProperty('IsPlayable', 'true')
                if subtitles: 
                    urls = re.compile('http:\/\/.*?\.srt').findall(subtitles)
                    item.setSubtitles(urls)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

            xbmcplugin.setContent(self.handle, 'movies')
            xbmcplugin.endOfDirectory(self.handle, True)


    def show_2(self, url, id_kp, title, image, genre, description, play):
        response = common.fetchPage({"link": url})
        if response["status"] != 200:
            return
        data_ = response["content"]
        url_ = url

        #serial
        serial = common.parseDOM(response["content"], "div", attrs={"class": "serial-panel"})
        if serial:
            seasonsbox = common.parseDOM(serial[0], "div", attrs={"class": "serial-season-box"})[0]
            seasons = common.parseDOM(seasonsbox, "option")
            for i, season in enumerate(seasons):
                title = self.encode(season)
                uri = sys.argv[0] + '?mode=serial&url=%s&season=%d&image=%s&id_kp=%s' % (url, i+1, image, id_kp)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={"title": title, "genre": genre, "plot": description})
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            xbmcplugin.setContent(self.handle, 'tvshows')
            xbmcplugin.endOfDirectory(self.handle, True)
            return

        else: 
            content = response["content"].split("$.ajax(")[-1].split("beforeSend")[0]
            content = content.split("data: {")[-1].split("},")[0]

            headers = {
                "Host": "kodik.cc",
                "Origin": "http://kodik.cc",
                "Referer": url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }
    
            values = {
                "domain": "cxz.by",
                "url": "http://cxz.by/online.php",
                "type": content.split('type: "')[-1].split('",')[0],         
                "hash": content.split('hash: "')[-1].split('",')[0],
                "id": content.split('id: "')[-1].split('",')[0],
                "quality": content.split('quality: "')[-1].split('",')[0]
            } 
            try: 
                request = urllib2.Request("http://kodik.cc/get-video", urllib.urlencode(values), headers)
                response = urllib2.urlopen(request).read()            
            except:
                manifest_links, subtitles = self.parse_alt(data_, url_)
                if manifest_links:
                    list = sorted(manifest_links.iteritems(), key=itemgetter(0))
                    for quality, link in list:
                        film_title = "%s [COLOR=FF00FF00][%s][/COLOR]" % (title, str(quality) + '')
                        uri = sys.argv[0] + '?mode=play&url=%s&pid=1' % urllib.quote(link)
                        item = xbmcgui.ListItem(film_title, iconImage=image)
                        item.setInfo(type='Video', infoLabels={'title': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                        item.setProperty('IsPlayable', 'true')
                        if subtitles: 
                            urls = re.compile('http:\/\/.*?\.srt').findall(subtitles)
                            item.setSubtitles(urls)
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
    
                    xbmcplugin.setContent(self.handle, 'movies')
                    xbmcplugin.endOfDirectory(self.handle, True)
                return
    
            if not response:
                return
            content = response.split('"qualities":{')[-1].split("}},")[0]

            qualities = ("360", "480", "720", "1080") 
            urlqlist = []
            for i, quality in enumerate(qualities):
                if ('"' + quality + '"') in content:
                    urlq = content.split('"' + quality + '":{"src":"')[-1].split('",')[0].replace("\/", "/")
                    if not (urlq in urlqlist):
                        urlqlist.append(urlq)
                        link_title = "%s [COLOR=FF00FF00][%s][/COLOR]" % (title, quality)
                        uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote_plus(urlq)
                        item = xbmcgui.ListItem(link_title,  iconImage=image, thumbnailImage=image)
                        item.setInfo(type='Video', infoLabels={"title": link_title, "genre": genre, "plot": description})
                        item.setProperty('IsPlayable', 'true')
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
    
            xbmcplugin.setContent(self.handle, 'movies')
            xbmcplugin.endOfDirectory(self.handle, True)


    def show(self, url, id_kp, title_, play = None):
        print "*** show for url %s " % url
        image, title, genre, description = self.get_media_info(id_kp, title_)
        if title_:
            title = title_

        if "moonwalk" in url:
            self.show_1(url, id_kp, title, image, genre, description, play)
        else:
            self.show_2(url, id_kp, title, image, genre, description, play)


    def play_item(self, url, pid = None):
        print "*** play url %s" % url

        if (pid == None) and ("m3u8" in url):
            url = ("http:" if (not ("http://" in url)) else "") + url
            response = common.fetchPage({"link": url})
            if (not (("http://" in response["content"]) or ("https://" in response["content"]))):
                content = response["content"].split("\n")
                name = os.path.join(self.path.decode("utf-8"), 'resources/playlists/') + "temp.m3u8"
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
        xbmcplugin.setResolvedUrl(self.handle, True, item)


    def get_user_input(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(2000))
        kbd.doModal()
        keyword = None
        if kbd.isConfirmed():
                keyword = kbd.getText()
        return keyword


    def search_category(self, url):
        keyword = self.get_user_input()
        if keyword:
            response = common.fetchPage({"link": url})

            if response["status"] == 200:
                content = response["content"]
                items = common.parseDOM(content, "li")
                links = common.parseDOM(items, "a", ret="href")
    
                for i, itemm in enumerate(items):
                    title = self.decorate_title(self.strip(itemm))
                    links = common.parseDOM(itemm, "a", ret="href")
                    if keyword.decode('utf-8').upper() in title.upper(): 
                        id_kp = itemm.split('onclick="id_kp(')[-1].split(');"')[0]
                        image = "http://st.kp.yandex.net/images/film/%s.jpg" % (id_kp) if id_kp else self.icon
                        uri = sys.argv[0] + '?mode=show&url=%s&url2=%s&id_kp=%s&title=%s' % (links[0], (links[1] if (len(links) > 1) else ""), id_kp, title)
                        item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
    
                xbmcplugin.setContent(self.handle, 'movies')
                xbmcplugin.endOfDirectory(self.handle, True)


    def search(self, keyword):
        keyword = keyword if (keyword) else self.get_user_input()
        if keyword:
            url = self.url + '/search_.php'

            values = {
                "name": keyword
            }

            headers = {
                "Host": "cxz.by",
                "Origin": self.url,
                "Referer": "http://cxz.by/online.php",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }

            request = urllib2.Request(url, urllib.urlencode(values), headers)
            response = urllib2.urlopen(request).read()

            items = common.parseDOM(response, "li")
            links = common.parseDOM(items, "a", ret="href")
            id_kps = common.parseDOM(items, "img", attrs={"title": "Info"}, ret="onclick")
            for i, item_ in enumerate(items):
                title = self.strip(item_)
                add = title.split("(")[-1].split(")")[0]
                add = self.strip(add + ", " + item_.split("<i>")[-1].split("</i>")[0].replace(":", ""))
                title = self.strip(item_.split("</i>")[-1].split("(")[0].strip())
                title = "%s [COLOR=55FFFFFF][%s][/COLOR]" % (title, add)
                id_kp = ""
                if len(id_kps) >= i+1:
                    id_kp = id_kps[i].split('id_kp(')[-1].split(')')[0]
                image = "http://st.kp.yandex.net/images/film/%s.jpg" % (id_kp) if id_kp else self.icon
                uri = sys.argv[0] + '?mode=show&url=%s&id_kp=%s&title=%s' % (links[i], id_kp, title)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            xbmcplugin.setContent(self.handle, 'movies')
            xbmcplugin.endOfDirectory(self.handle, True)


    # *** Add-on helpers
    def log(self, message):
        if self.debug:
            print "### %s: %s" % (self.id, message)

    def error(self, message):
        print "%s ERROR: %s" % (self.id, message)

    def showErrorMessage(self, msg):
        print msg
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(5 * 1000)))

    def strip(self, string):
        return common.stripTags(string)

    def encode(self, string):
        return string.decode('cp1251').encode('utf-8')

    def decode(self, string):
        return string.decode('utf-8').encode('cp1251')

    def strip(self, string):
        return common.stripTags(string)

PopcornBY = PopcornBY()
PopcornBY.main()
