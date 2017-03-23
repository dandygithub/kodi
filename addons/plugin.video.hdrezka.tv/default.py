#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Writer (c) 2012-2017, MrStealth, dandy
# Rev. 2.0.0

import os, urllib, urllib2, sys #, socket, cookielib, errno
import xbmc, xbmcplugin,xbmcgui,xbmcaddon
import re, json
from operator import itemgetter

import XbmcHelpers
common = XbmcHelpers

import Translit as translit
translit = translit.Translit()

try:
    sys.path.append(os.path.dirname(__file__)+ '/../plugin.video.unified.search')
    from unified_search import UnifiedSearch
except:
    pass

class HdrezkaTV():
    def __init__(self):
        self.id = 'plugin.video.hdrezka.tv'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString
        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.handle = int(sys.argv[1])
        self.url = 'http://hdrezka.me'

        self.quality = self.addon.getSetting('quality')

    def main(self):
        params = common.getParameters(sys.argv[2])
        mode = url = page = None

        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        urlm = urllib.unquote_plus(params['urlm']) if 'urlm' in params else None
        page = int(params['page']) if 'page' in params else 1

        post_id = params['post_id'] if 'post_id' in params else None
        season_id = params['season_id'] if 'season_id' in params else None
        episode_id = params['episode_id'] if 'episode_id' in params else None
        title = urllib.unquote_plus(params['title']) if 'title' in params else None
        image = params['image'] if 'image' in params else None

        keyword = params['keyword'] if 'keyword' in params else None
        external = 'unified' if 'unified' in params else None
        if external == None:
            external = 'usearch' if 'usearch' in params else None    

        if mode == 'play':
            self.play(url)
        if mode == 'play_episode':
            self.play_episode(url, urlm, post_id, season_id, episode_id, title, image)
        if mode == 'show':
            self.show(url)
        if mode == 'index':
            self.index(url, page)
        if mode == 'categories':
            self.categories()
        if mode == 'search':
            self.search(keyword, external)
        elif mode == None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("categories", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1003), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.index('http://hdrezka.me/films', 1)

    def categories(self):
        response = common.fetchPage({"link": self.url})
        genres = common.parseDOM(response["content"], "ul", attrs={"id": "topnav-menu"})

        titles = common.parseDOM(genres, "a", attrs={"class": "b-topnav__item-link"})
        links = common.parseDOM(genres, "a", attrs={"class": "b-topnav__item-link"}, ret='href')

        for i, title in enumerate(titles):
            title = common.stripTags(title)
            link = self.url + links[i]

            uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", link)
            item = xbmcgui.ListItem(title, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def sub_categories(self, category_id):
        response = common.fetchPage({"link": self.url})
        genres = common.parseDOM(response["content"], "ul", attrs={"id": "topnav-menu"})

        titles = common.parseDOM(genres, "a")
        links = common.parseDOM(genres, "a", ret='href')

        for i, title in enumerate(titles):
            if 'http' in links[i]:
                link = links[i]
            else:
                link = self.url + links[i]

            uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", link)
            item = xbmcgui.ListItem(title, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)


    def index(self, url, page):
        if(page == 1):
            page_url = url
        else:
            page_url = "%s/page/%s/" % (url, page)

        print page_url

        response = common.fetchPage({"link": page_url})
        content = common.parseDOM(response["content"], "div", attrs={"class": "b-content__inline_items"})
        items = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"})
        post_ids = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"}, ret="data-id")

        link_containers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-link"})

        links = common.parseDOM(link_containers, "a", ret='href')
        titles = common.parseDOM(link_containers, "a")
        divcovers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-cover"})

        country_years = common.parseDOM(link_containers, "div")
        items_count = 0

        for i, title in enumerate(titles):
            items_count += 1

            infos = self.get_item_description(url, post_ids[i])

            country_year = country_years[i].split(',')[0].replace('.', '').replace('-', '').replace(' ', '')
            title = "%s [COLOR=55FFFFFF](%s)[/COLOR]" % (title, country_year)
            image = common.parseDOM(divcovers[i], "img", ret='src')[0]

            uri = sys.argv[0] + '?mode=show&url=%s' % links[i]
            item = xbmcgui.ListItem(title, iconImage=image)
            item.setInfo(type='Video', infoLabels={'title': title, 'genre': country_years[i], 'plot': infos['description'], 'rating': infos['rating']})
            if (self.quality != 'select') and (not ('/series/' in url)) and (not ('/show/' in url)):
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
            else:
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        if not items_count < 16:
            uri = sys.argv[0] + '?mode=%s&url=%s&page=%s' % ("index", url, str(int(page) + 1))
            item = xbmcgui.ListItem(self.language(1004), iconImage=self.inext)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def selectQuality(self, links, title, image):
        if self.quality != 'select': 
            self.play(links[self.quality])
        else:
            list = sorted(links.iteritems(), key=itemgetter(0))
            for quality, link in list:
                print "quality: %s link %s" % (quality, link)
                film_title = "%s (%s)" % (title, quality)
                uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote(link)
                item = xbmcgui.ListItem(film_title, iconImage=image)
                item.setInfo(type='Video', infoLabels={'title': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

    def show(self, url):
        print "Get video %s" % url
        response = common.fetchPage({"link": url})

        content = common.parseDOM(response["content"], "div", attrs={"id": "wrapper"})
        image_container = common.parseDOM(content, "div", attrs={"class": "b-sidecover"})

        title = common.parseDOM(content, "h1")[0]
        image = common.parseDOM(image_container, "img", ret='src')[0]

        playlist = common.parseDOM(content, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        post_id = common.parseDOM(content, "input", attrs={"id": "post_id" }, ret="value")[0]

        titles = common.parseDOM(playlist, "li")
        ids = common.parseDOM(playlist, "li", ret='data-id')
        seasons = common.parseDOM(playlist, "li", ret='data-season_id')
        episodes = common.parseDOM(playlist, "li", ret='data-episode_id')

        print "POST ID %s " % post_id
        print "Image %s" % image

        if playlist:
            print "This is a season"
            videoplayer = common.parseDOM(content, 'div', attrs={'id': 'videoplayer'})
            iframe = common.parseDOM(content, 'iframe', ret='src')[0]
            for i, title in enumerate(titles):
                title = "%s (%s %s)" % (title, self.language(1005), seasons[i])
                url_episode = iframe.split("?")[0] + "?nocontrols=1&season=%s&episode=%s" % (seasons[i], episodes[i])
                uri = sys.argv[0] + '?mode=play_episode&url=%s&urlm=%s&post_id=%s&season_id=%s&episode_id=%s&title=%s&image=%s' % (url_episode, url, ids[i], seasons[i], episodes[i], title, image)
                item = xbmcgui.ListItem(title, iconImage=image)
                if self.quality != 'select':
                    item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True if self.quality == 'select' else False)
        else:
            try:
                link = self.get_video_link(url, post_id)

                uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote(link)
                item = xbmcgui.ListItem(title, iconImage=image)
                item.setInfo(type='Video', infoLabels={'title': title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

            except ValueError:
                print "GET LINK FROM IFRAME"
                videoplayer = common.parseDOM(content, 'div', attrs={'id': 'videoplayer'})
                iframe = common.parseDOM(content, 'iframe', ret='src')[0]
                links = self.get_video_link_from_iframe(iframe, url)
                self.selectQuality(links, title, image)

        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def get_item_description(self, referer, post_id):
        url = 'http://hdrezka.me/engine/ajax/quick_content.php'

        headers = {
            "Accept" : "text/plain, */*; q=0.01",
            "Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Host" : "hdrezka.me",
            "Referer" : referer,
            "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:27.0) Gecko/20100101 Firefox/27.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = urllib.urlencode({
            "id" : post_id,
            "is_touch" : 0
        })

        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request).read()

        description = common.parseDOM(response, 'div', attrs={'class': 'b-content__bubble_text'})[0]

        try:
            imbd_rating = common.parseDOM(response, 'span', attrs={'class': 'imdb'})[0]
            rating = common.parseDOM(imbd_rating, 'b')[0]
        except IndexError, e:
            try:
                imbd_rating = common.parseDOM(response, 'span', attrs={'class': 'kp'})[0]
                rating = common.parseDOM(imbd_rating, 'b')[0]
            except IndexError, e:
                rating = 0

        return { 'rating' : rating, 'description' : description }

    def get_video_link_from_iframe(self, url, mainurl):

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
            "Referer": mainurl
        }

        request = urllib2.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
        
        purl =  response.split("var window_surl = '")[-1].split("';")[0]
        params = response.split("var banners_script_clickunder = {")[-1].split("};")[0]

        data = urllib.urlencode({
            "video_token" : params.split("video_token: '")[-1].split("',")[0],
            "content_type": params.split("content_type: '")[-1].split("',")[0],
            "mw_key" : params.split("mw_key: '")[-1].split("',")[0],
            "mw_pid": params.split("mw_pid: ")[-1].split(",")[0],
            "p_domain_id" : params.split("p_domain_id: ")[-1].split(",")[0],
            "ad_attr": "0",
            "debug": "false",
            "detect_true" : response.split("var detect_true = '")[-1].split("';")[0],
        })

        headers = {
            "Host": "s6.cdnapponline.com",
            "Connection": "keep-alive",
            "Origin": "http://s6.cdnapponline.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
            "Referer": url,
            "X-Mega-Version": "505",
            "X-Requested-With": "XMLHttpRequest"
        }

        request = urllib2.Request('http://s6.cdnapponline.com' + purl, data, headers)
        response = urllib2.urlopen(request).read()

        data = json.loads(response.decode('unicode-escape'))
        playlisturl = data['mans']['manifest_m3u8']
        response = common.fetchPage({"link": playlisturl})['content']
#EXTM3U
                                            #EXT-X-STREAM-INF:RESOLUTION=640x360,BANDWIDTH=376000
#                                            http://185.38.12.60/sec/1490124744/363937351e999321d7e55abd91062b15ad2e2fce4e564a70/ivs/d3/b8/c15ce5c350bb/hls/tracks-3,4/index.m3u8
                                            #EXT-X-STREAM-INF:RESOLUTION=852x480,BANDWIDTH=571000
#                                            http://185.38.12.60/sec/1490124744/33323039e230fadb41f8ceec3f073d0728c48230a8add77d/ivs/d3/b8/c15ce5c350bb/hls/tracks-2,4/index.m3u8
                                            #EXT-X-STREAM-INF:RESOLUTION=1280x720,BANDWIDTH=1038000
#                                            http://185.38.12.60/sec/1490124744/34393338c60b1ea171fc69d5612ae0717389dcf0e7e30f6a/ivs/d3/b8/c15ce5c350bb/hls/tracks-1,4/index.m3u8

        #{"mans":{"manifest_f4m":"http://streamblast.cc/video/e037e4450736bb38/manifest.f4m?cd=0&expired=1490102271&mw_pid=157&signature=e0a48062dc0a3b63c7ffcd9f2de08ba0","manifest_m3u8":"http://streamblast.cc/video/e037e4450736bb38/index.m3u8?cd=0&expired=1490102271&mw_pid=157&signature=e0a48062dc0a3b63c7ffcd9f2de08ba0","manifest_dash":"http://streamblast.cc/video/e037e4450736bb38/manifest.mpd?cd=0&expired=1490102271&mw_pid=157&signature=e0a48062dc0a3b63c7ffcd9f2de08ba0","manifest_mp4":null}}
        urls = re.compile("http:\/\/.*?\n").findall(response)
        manifest_links = {}
        manifest_links['360p'] = urls[0].replace("\n", "")
        manifest_links['480p'] = urls[1].replace("\n", "")
        manifest_links['720p'] = urls[2].replace("\n", "")

#        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', response)
#        links = []
#        manifest_links = {}

#        for url in urls:
#            if 'mp4' in url:
#                links.append(url)

#        for link in links:
#            if 'manifest' in link:
#                if '360' in link:
#                    manifest_links['360p'] = link.replace("',", '').replace("manifest.f4m", 'index.m3u8')
#                elif '480':
#                    manifest_links['480p'] = link.replace("',", '').replace("manifest.f4m", 'index.m3u8')
#                elif '720':
#                    manifest_links['720p'] = link.replace("',", '').replace("manifest.f4m", 'index.m3u8')

        return manifest_links

    def get_video_link(self, referer, post_id):
        url = 'http://hdrezka.me/engine/ajax/getvideo.php'

        headers = {
            "Accept" : "text/plain, */*; q=0.01",
            "Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Host" : "hdrezka.me",
            "Referer" : referer,
            "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:27.0) Gecko/20100101 Firefox/27.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = urllib.urlencode({
            "id" : post_id
        })

        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)

        response = json.loads(response.read().encode("utf-8"))
        links = json.loads(response['link'].encode("utf-8"))
        return links['hls']

    def get_seaons_link(self, referer, video_id, season, episode):
        url = 'http://hdrezka.me/engine/ajax/getvideo.php'

        headers = {
            "Accept" : "text/plain, */*; q=0.01",
            "Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Host" : "hdrezka.me",
            "Referer" : referer,
            "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:27.0) Gecko/20100101 Firefox/27.0",
            "X-Requested-With" : "XMLHttpRequest"
        }

        data = urllib.urlencode({
            'id': video_id,
            'season':  season,
            'episode': episode
        })

        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)

        response = json.loads(response.read().encode("utf-8"))
        links = json.loads(response['link'].encode("utf-8"))
        return links['hls']

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

    def search(self, keyword, external):
        print "*** Search"

        keyword = keyword if (external != None) else self.getUserInput()
        keyword = translit.rus(keyword) if (external == 'unified') else urllib.unquote_plus(keyword)
        unified_search_results = []

        if keyword:
            print keyword
            
            url = 'http://hdrezka.me/index.php?do=search&subaction=search&q=%s' % (keyword)

            headers = {
                'Host': 'hdrezka.me',
                'Referer': 'http://hdrezka.me/',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
            }

            request = urllib2.Request(url, "", headers)
            request.get_method = lambda: 'GET'
            response = urllib2.urlopen(request).read()

#<div class="b-content__inline b-content__search_wrapper"> 
#<div class="b-content__inline_inner b-content__inline_inner_mainprobar clearfix"> 
#<div class="b-content__inline_items"> 
#<div class="b-content__inline_item" data-id="1984" data-url="http://hdrezka.me/series/fiction/1984-sotnya.html"> 
#<div class="b-content__inline_item-cover"> 
#<a href="http://hdrezka.me/series/fiction/1984-sotnya.html"> 
#<img src="http://static.hdrezka.me/i/2014/8/26/r98bc8a403718bx87e98k.jpg" height="250" width="166" alt="Сотня" /> 
#<span class="cat series">
#<i class="entity">Сериал</i>
#<i class="icon"></i>
#</span> 
#<span class="info">4 сезон, 6 серия</span> 
#<i class="i-sprt play"></i> 
#</a> 
#<i class="trailer show-trailer" data-id="1984" data-full="1"><b>Смотреть трейлер</b></i> </div> 
#<div class="b-content__inline_item-link"> 
#<a href="http://hdrezka.me/series/fiction/1984-sotnya.html">Сотня</a> 
#<div>2014 - ..., США, Фантастика</div> 
#</div>
#</div>

            content = common.parseDOM(response, "div", attrs={"class": "b-content__inline_items"})
            videos = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"})

            for i, videoitem in enumerate(videos):
                link = common.parseDOM(videoitem, "a", ret='href')[0]
                title = common.parseDOM(videoitem, "a")[1]
                image = common.parseDOM(videoitem, "img", ret='src')[0]
                descriptiondiv = common.parseDOM(videoitem, "div", attrs={"class": "b-content__inline_item-link"})[0]
                description = common.parseDOM(descriptiondiv, "div")[0]

                if (external == 'unified'):
                    print "Perform unified search and return results"
                    unified_search_results.append({'title':  title, 'url': link, 'image': image, 'plugin': self.id})
                else:
                    uri = sys.argv[0] + '?mode=show&url=%s' % urllib.quote(link)
                    item = xbmcgui.ListItem("%s [COLOR=55FFFFFF][%s][/COLOR]" % (title, description), iconImage=image)
                    item.setInfo(type='Video', infoLabels={'title': title})
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if (external == 'unified'):
                UnifiedSearch().collect(unified_search_results)
            else:
                xbmcplugin.setContent(self.handle, 'movies')
                xbmcplugin.endOfDirectory(self.handle, True)
        else:
            self.menu()

    def play(self, url):
        item = xbmcgui.ListItem(path = url)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def play_episode(self, url, referer, post_id, season_id, episode_id, title, image):
        print "***** play_season"
        try:
            url = self.get_seaons_link(referer, post_id, season_id, episode_id)

            item = xbmcgui.ListItem(path = url)
            xbmcplugin.setResolvedUrl(self.handle, True, item)

        except:
            print "GET LINK FROM IFRAME"
            links = self.get_video_link_from_iframe(url, referer)
            self.selectQuality(links, title, image)
            xbmcplugin.setContent(self.handle, 'episodes')
            xbmcplugin.endOfDirectory(self.handle, True)


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

plugin = HdrezkaTV()
plugin.main()
