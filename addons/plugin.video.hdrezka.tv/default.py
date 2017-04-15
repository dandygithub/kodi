#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Writer (c) 2012-2017, MrStealth, dandy
# Rev. 2.1.0

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

QUALITY_TYPES = (360, 480, 720, 1080)

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
        self.translator = self.addon.getSetting('translator') if self.addon.getSetting('translator') else "default"

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
            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
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

    def selectQuality(self, links, title, image, subtitles = None):
        if self.quality != 'select': 
            try:
                self.play(links[int(self.quality[:-1])], subtitles)
            except:
                self.play(links[720], subtitles)
        else:
            list = sorted(links.iteritems(), key=itemgetter(0))
            for quality, link in list:
                print "quality: %s link %s" % (quality, link)
                film_title = "%s (%s)" % (title, str(quality) + 'p')
                uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote(link)
                item = xbmcgui.ListItem(film_title, iconImage=image)
                item.setInfo(type='Video', infoLabels={'title': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                item.setProperty('IsPlayable', 'true')
                if subtitles: 
                    urls = re.compile('http:\/\/.*?\.srt').findall(subtitles)
                    item.setSubtitles(urls)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

#<ul id="translators-list" class="b-translators__list"><li title="Kerob (Coldfilm)" class="b-translator__item active" data-translator_id="35">Kerob (Coldfilm)</li><li title="ViruseProject" class="b-translator__item" data-translator_id="47">ViruseProject</li></ul>

#http://hdrezka.me/ajax/get_cdn_series/?t=1491681866585

#id:24193
#translator_id:47

#Host:hdrezka.me
#Origin:http://hdrezka.me
#Referer:http://hdrezka.me/series/thriller/24193-v-rozyske-ty-v-rozyske.html
#User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36
#X-Requested-With:XMLHttpRequest

#{"success":true,"message":"","seasons":"\u003Cli class=\"b-simple_season__item active\" data-restricted=\"0\" data-tab_id=\"1\"\u003E\u0421\u0435\u0437\u043e\u043d 1\u003C\/li\u003E","episodes":"\u003Cul id=\"simple-episodes-list-1\" class=\"b-simple_episodes__list clearfix\"\u003E\u003Cli class=\"b-simple_episode__item active\" data-restricted=\"0\" data-id=\"24193\" data-season_id=\"1\" data-episode_id=\"1\"\u003E\u0421\u0435\u0440\u0438\u044f 1\u003C\/li\u003E\u003Cli class=\"b-simple_episode__item\" data-restricted=\"0\" data-id=\"24193\" data-season_id=\"1\" data-episode_id=\"2\"\u003E\u0421\u0435\u0440\u0438\u044f 2\u003C\/li\u003E\u003Cli class=\"b-simple_episode__item\" data-restricted=\"0\" data-id=\"24193\" data-season_id=\"1\" data-episode_id=\"3\"\u003E\u0421\u0435\u0440\u0438\u044f 3\u003C\/li\u003E\u003Cli class=\"b-simple_episode__item\" data-restricted=\"0\" data-id=\"24193\" data-season_id=\"1\" data-episode_id=\"4\"\u003E\u0421\u0435\u0440\u0438\u044f 4\u003C\/li\u003E\u003C\/ul\u003E","url":"http:\/\/s4.cdnapponline.com\/serial\/29ae8190e45bed1f9e5adfb1f4fd4dbf\/iframe","player":"\u003Ciframe id=\"cdn-player\" src=\"http:\/\/s4.cdnapponline.com\/serial\/29ae8190e45bed1f9e5adfb1f4fd4dbf\/iframe?nocontrols=1&season=1&episode=1\" name=\"it1491681871\" width=\"640\" height=\"360\" frameborder=\"0\" allowfullscreen webkitallowfullscreen mozallowfullscreen oallowfullscreen msallowfullscreen\u003E\u003C\/iframe\u003E"}

    def selectTranslator(self, content, post_id):
        iframe0 = common.parseDOM(content, 'iframe', ret='src')[0]
        try:
            playlist0 = common.parseDOM(content, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        except:
            playlist0 = ""  
        try:
            div = common.parseDOM(content, 'ul', attrs={'id': 'translators-list'})[0]
        except:
            return iframe0, playlist0
        titles = common.parseDOM(div, 'li')
        ids = common.parseDOM(div, 'li', ret = "data-translator_id")
        if len(titles) > 1:
            dialog = xbmcgui.Dialog()
            index_ = dialog.select(self.language(1006), titles)
            if int(index_) < 0:
                index_ = 0    
        else:
            index_ = 0    
        idt = ids[index_]

        headers = {
            "Host": "hdrezka.me",
            "Origin": "http://hdrezka.me",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }

        values = {
            "id": post_id,
            "translator_id": idt
        }

        request = urllib2.Request("http://hdrezka.me/ajax/get_cdn_series/", urllib.urlencode(values), headers)
        response = urllib2.urlopen(request).read()

        data = json.loads(response)
        player = data["player"]
        seasons = data["seasons"]
        episodes = data["episodes"]
        iframe = common.parseDOM(player, 'iframe', ret='src')[0]
        playlist = common.parseDOM(episodes, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        return iframe, playlist

#player=u'<iframe id="cdn-player" src="http://s4.cdnapponline.com/serial/df88dab4dcdde657bc7b6142b2c22afc/iframe?nocontrols=1&season=1&episode=1" name="it1491779049" width="640" height="360" frameborder="0" allowfullscreen webkitallowfullscreen mozallowfullscreen oallowfullscreen msallowfullscreen></iframe>'
#seasons=u'<li class="b-simple_season__item active" data-restricted="0" data-tab_id="1">\u0421\u0435\u0437\u043e\u043d 1</li><li class="b-simple_season__item" data-restricted="0" data-tab_id="3">\u0421\u0435\u0437\u043e\u043d 3</li><li class="b-simple_season__item" data-restricted="0" data-tab_id="4">\u0421\u0435\u0437\u043e\u043d 4</li>'
#episodes=u'<ul id="simple-episodes-list-1" class="b-simple_episodes__list clearfix"><li class="b-simple_episode__item active" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="1">\u0421\u0435\u0440\u0438\u044f 1</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="2">\u0421\u0435\u0440\u0438\u044f 2</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="3">\u0421\u0435\u0440\u0438\u044f 3</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="4">\u0421\u0435\u0440\u0438\u044f 4</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="5">\u0421\u0435\u0440\u0438\u044f 5</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="6">\u0421\u0435\u0440\u0438\u044f 6</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="7">\u0421\u0435\u0440\u0438\u044f 7</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="8">\u0421\u0435\u0440\u0438\u044f 8</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="9">\u0421\u0435\u0440\u0438\u044f 9</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="10">\u0421\u0435\u0440\u0438\u044f 10</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="11">\u0421\u0435\u0440\u0438\u044f 11</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="12">\u0421\u0435\u0440\u0438\u044f 12</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="1" data-episode_id="13">\u0421\u0435\u0440\u0438\u044f 13</li></ul><ul id="simple-episodes-list-3" class="b-simple_episodes__list clearfix" style="display: none;"><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="1">\u0421\u0435\u0440\u0438\u044f 1</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="2">\u0421\u0435\u0440\u0438\u044f 2</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="3">\u0421\u0435\u0440\u0438\u044f 3</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="4">\u0421\u0435\u0440\u0438\u044f 4</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="5">\u0421\u0435\u0440\u0438\u044f 5</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="6">\u0421\u0435\u0440\u0438\u044f 6</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="7">\u0421\u0435\u0440\u0438\u044f 7</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="8">\u0421\u0435\u0440\u0438\u044f 8</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="9">\u0421\u0435\u0440\u0438\u044f 9</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="10">\u0421\u0435\u0440\u0438\u044f 10</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="11">\u0421\u0435\u0440\u0438\u044f 11</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="12">\u0421\u0435\u0440\u0438\u044f 12</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="13">\u0421\u0435\u0440\u0438\u044f 13</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="14">\u0421\u0435\u0440\u0438\u044f 14</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="15">\u0421\u0435\u0440\u0438\u044f 15</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="3" data-episode_id="16">\u0421\u0435\u0440\u0438\u044f 16</li></ul><ul id="simple-episodes-list-4" class="b-simple_episodes__list clearfix" style="display: none;"><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="4" data-episode_id="1">\u0421\u0435\u0440\u0438\u044f 1</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="4" data-episode_id="2">\u0421\u0435\u0440\u0438\u044f 2</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="4" data-episode_id="3">\u0421\u0435\u0440\u0438\u044f 3</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="4" data-episode_id="4">\u0421\u0435\u0440\u0438\u044f 4</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="4" data-episode_id="5">\u0421\u0435\u0440\u0438\u044f 5</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="4" data-episode_id="6">\u0421\u0435\u0440\u0438\u044f 6</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="4" data-episode_id="7">\u0421\u0435\u0440\u0438\u044f 7</li><li class="b-simple_episode__item" data-restricted="0" data-id="1984" data-season_id="4" data-episode_id="8">\u0421\u0435\u0440\u0438\u044f 8</li></ul>'

    def show(self, url):
        print "Get video %s" % url
        response = common.fetchPage({"link": url})

        content = common.parseDOM(response["content"], "div", attrs={"id": "wrapper"})
        image_container = common.parseDOM(content, "div", attrs={"class": "b-sidecover"})
        title = common.parseDOM(content, "h1")[0]
        image = common.parseDOM(image_container, "img", ret='src')[0]
        post_id = common.parseDOM(content, "input", attrs={"id": "post_id" }, ret="value")[0]

        playlist = common.parseDOM(content, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        iframe = common.parseDOM(content, 'iframe', ret='src')[0]
        if playlist:
            if self.translator == "select":
                iframe, playlist = self.selectTranslator(content, post_id)
            titles = common.parseDOM(playlist, "li")
            ids = common.parseDOM(playlist, "li", ret='data-id')
            seasons = common.parseDOM(playlist, "li", ret='data-season_id')
            episodes = common.parseDOM(playlist, "li", ret='data-episode_id')

        print "POST ID %s " % post_id
        #print "Image %s" % image

        if playlist:
            #print "This is a season"
            videoplayer = common.parseDOM(content, 'div', attrs={'id': 'videoplayer'})
            for i, title in enumerate(titles):
                title = "%s (%s %s)" % (title, self.language(1005), seasons[i])
                url_episode = iframe.split("?")[0]
                uri = sys.argv[0] + '?mode=play_episode&url=%s&urlm=%s&post_id=%s&season_id=%s&episode_id=%s&title=%s&image=%s' % (url_episode, url, ids[i], seasons[i], episodes[i], title, image)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                if self.quality != 'select':
                    item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True if self.quality == 'select' else False)
        else:
            try:
                link = self.get_video_link(url, post_id)

                uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote(link)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0})
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

            except ValueError:
                print "GET LINK FROM IFRAME"
                videoplayer = common.parseDOM(content, 'div', attrs={'id': 'videoplayer'})
                iframe = common.parseDOM(content, 'iframe', ret='src')[0]
                links, subtitles = self.get_video_link_from_iframe(iframe, url)
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


    def getKey(self, content):
        key = ''
        value = '' 
        try:  
            script = content.split("setTimeout(function()")[-1].split("</script>")[0]    
            key = script.split("['")[-1].split("'] = '")[0]    
            value = script.split("'] = '")[-1].split("';")[0]    
        except:
            pass 
        return key, value

    def getAccessAttrs(self, content):
        attrs = {}
        purl = content.split("var window_surl = '")[-1].split("';")[0]
        attrs['mw_key'] = content.split("var mw_key = '")[-1].split("';")[0] 
        attrs['video_token'] = content.split("video_token: '")[-1].split("',")[0] 
        attrs['mw_pid'] = content.split("mw_pid: ")[-1].split(",")[0] 
        attrs['p_domain_id'] = content.split("p_domain_id: ")[-1].split(",")[0] 
        attrs['ad_attr'] = '0'
        attrs['debug'] = 'false'

        key, value = self.getKey(content) 

        attrs[key] = value

        return purl, attrs


    def get_video_link_from_iframe(self, url, mainurl):

        playlist_domain = 's4.cdnapponline.com'

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
            "Referer": mainurl
        }

        request = urllib2.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        subtitles = None
        if "var subtitles = JSON.stringify(" in response:
            subtitles = response.split("var subtitles = JSON.stringify(")[-1].split(");")[0]

        purl, values = self.getAccessAttrs(response)

        headers = {
            "Host": playlist_domain,
            "Origin": "http://" + playlist_domain,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            "Referer": url,
            "X-Requested-With": "XMLHttpRequest"
        }

        request = urllib2.Request('http://' + playlist_domain + purl, urllib.urlencode(values), headers)
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
        for i, url in enumerate(urls):
            manifest_links[QUALITY_TYPES[i]] = url.replace("\n", "")

        return manifest_links, subtitles

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

            headers = {
                'Host': 'hdrezka.me',
                'Referer': 'http://hdrezka.me/',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
            }

            values = {
                "do": "search",
                "subaction": "search",
                "q": unicode(keyword)
            }

            form = urllib.urlencode(values)
            encoded_kwargs = urllib.urlencode(values.items())
            argStr = "/?%s" %(encoded_kwargs)
            request = urllib2.Request(self.url + argStr, "", headers)
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
                    item = xbmcgui.ListItem("%s [COLOR=55FFFFFF][%s][/COLOR]" % (title, description), iconImage=image, thumbnailImage=image)
                    item.setInfo(type='Video', infoLabels={'title': title})
                    if (self.quality != 'select') and (not ('/series/' in link)) and (not ('/show/' in link)):
                        item.setProperty('IsPlayable', 'true')
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
                    else:
                        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if (external == 'unified'):
                UnifiedSearch().collect(unified_search_results)
            else:
                xbmcplugin.setContent(self.handle, 'movies')
                xbmcplugin.endOfDirectory(self.handle, True)
        else:
            self.menu()

    def play(self, url, subtitles = None):
        item = xbmcgui.ListItem(path = url)
        if subtitles:
            urls = re.compile('http:\/\/.*?\.srt').findall(subtitles)
            item.setSubtitles(urls)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def play_episode(self, url, referer, post_id, season_id, episode_id, title, image):
        print "***** play_season"
        try:
            url = self.get_seaons_link(referer, post_id, season_id, episode_id)

            item = xbmcgui.ListItem(path = url)
            xbmcplugin.setResolvedUrl(self.handle, True, item)

        except:
            print "GET LINK FROM IFRAME"
            url_episode = url + "?nocontrols=1&season=%s&episode=%s" % (season_id, episode_id)
            links, subtitles = self.get_video_link_from_iframe(url_episode, referer)
            self.selectQuality(links, title, image, subtitles)
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
