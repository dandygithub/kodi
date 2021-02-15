#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Writer (c) 2012-2019, MrStealth, dandy
# Rev. 2.3.0

import json
import os
import re
import socket
import sys
import urllib
import urllib2
from operator import itemgetter
import requests

from Translit import Translit
import XbmcHelpers
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from videohosts import moonwalk
import SearchHistory as history

common = XbmcHelpers
transliterate = Translit()

socket.setdefaulttimeout(120)

USER_AGENT = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0"
PLAYLIST_DOMAIN = 's9.cdnapponline.com'
QUALITY_TYPES = (360, 480, 720, 1080, 2160)


class HdrezkaTV:
    def __init__(self):
        self.id = 'plugin.video.hdrezka.tv'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')

        self.language = self.addon.getLocalizedString
        self.inext = os.path.join(self.addon.getAddonInfo('path'), 'resources/icons/next.png')
        self.handle = int(sys.argv[1])
        self.dom_protocol = self.addon.getSetting('dom_protocol')
        self.domain = self.addon.getSetting('domain')
        self.url = self.dom_protocol + '://' + self.domain
        self.proxies = self._load_proxy_settings()
        self.quality = self.addon.getSetting('quality')
        self.translator = self.addon.getSetting('translator')
        self.description = self.addon.getSetting('description')

    def _load_proxy_settings(self):
        if self.addon.getSetting('use_proxy') == 'false':
            return False
        proxy_protocol = self.addon.getSetting('protocol')
        proxy_url = self.addon.getSetting('proxy_url')
        return {
            'http': proxy_protocol + '://' + proxy_url,
            'https': proxy_protocol + '://' + proxy_url
        }

    def get_response(self, url, data=None, headers=None, cookies=None, referer='http://www.random.org'):
        if not headers:
            headers = {
                "Host": self.domain,
                "Referer": referer,
                "User-Agent": USER_AGENT,
            }
        return requests.get(url, params=data, headers=headers, cookies=cookies, proxies=self.proxies)

    def post_response(self, url, data=None, headers=None, cookies=None, referer='http://www.random.org'):
        if not headers:
            headers = {
                "Host": self.domain,
                "Referer": referer,
                "User-Agent": USER_AGENT,
            }
        return requests.post(url, data=data, headers=headers, cookies=cookies, proxies=self.proxies)

    def main(self):
        params = common.getParameters(sys.argv[2])
        mode = params.get('mode')
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        external = 'main' if 'main' in params else None
        if not external:
            external = 'usearch' if 'usearch' in params else None

        if mode == 'play':
            self.play(url)
        if mode == 'play_episode':
            self.play_episode(
                url,
                urllib.unquote_plus(params['urlm']),
                params.get('post_id'),
                params.get('season_id'),
                params.get('episode_id'),
                urllib.unquote_plus(params['title']),
                params.get('image'),
                params.get('idt'),
                urllib.unquote_plus(params['data'])
            )
        if mode == 'show':
            self.show(url)
        if mode == 'index':
            self.index(url, int(params.get('page', 1)))
        if mode == 'categories':
            self.categories()
        if mode == 'sub_categories':
            self.sub_categories(url)
        if mode == 'search':
            self.search(params.get('keyword'), external)
        if mode == 'history':
            self.history()
        if mode == 'collections':
            self.collections(int(params.get('page', 1)))
        elif mode is None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("history", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00][%s][/COLOR]" % self.language(1008), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("categories", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % self.language(1003), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.index(self.url + '/films', 1)

    def categories(self):
        response = self.get_response(self.url)
        genres = common.parseDOM(response.text, "ul", attrs={"id": "topnav-menu"})

        titles = common.parseDOM(genres, "a", attrs={"class": "b-topnav__item-link"})
        links = common.parseDOM(genres, "a", attrs={"class": "b-topnav__item-link"}, ret='href')
        for i, title in enumerate(titles):
            title = common.stripTags(title)
            link = self.url + links[i]
            uri = sys.argv[0] + '?mode=%s&url=%s' % ("sub_categories", link)
            item = xbmcgui.ListItem(title, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&page=%d' % ("collections", 1)
        item = xbmcgui.ListItem('Подборки', thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def sub_categories(self, url):
        response = self.get_response(url)
        genres = common.parseDOM(response.text, "ul", attrs={"class": "left"})

        titles = common.parseDOM(genres, "a")
        links = common.parseDOM(genres, "a", ret='href')

        clean_url = url.replace(self.url, '')

        uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", url)
        item = xbmcgui.ListItem('[COLOR=FF00FFF0][%s][/COLOR]' % self.language(1007), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        for i, title in enumerate(titles):
            if not links[i].startswith(clean_url):
                continue
            link = self.url + links[i]
            uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", link)
            item = xbmcgui.ListItem(title, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def collections(self, page):
        page_url = '/collections/'
        if page != 1:
            page_url = "/collections/page/%s/" % page

        response = self.get_response(self.url + page_url)
        content = common.parseDOM(response.text, 'div', attrs={'class': 'b-content__collections_list clearfix'})
        titles = common.parseDOM(content, "a", attrs={"class": "title"})
        counts = common.parseDOM(content, 'div', attrs={"class": ".num"})
        links = common.parseDOM(content, "div", attrs={"class": "b-content__collections_item"}, ret="data-url")
        icons = common.parseDOM(content, "img", attrs={"class": "cover"}, ret="src")

        for i, name in enumerate(titles):
            link = self.url + links[i].replace(self.url, '')
            uri = sys.argv[0] + '?mode=%s&url=%s' % ("index", link)
            item = xbmcgui.ListItem('%s [COLOR=55FFFFFF](%s)[/COLOR]' % (name, counts[i]), thumbnailImage=icons[i])
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        if not len(titles) < 32:
            uri = sys.argv[0] + '?mode=%s&page=%d' % ("collections", page + 1)
            item = xbmcgui.ListItem(self.language(1004), iconImage=self.inext)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def index(self, url, page):
        response = self.get_response("%s/page/%s/" % (url, page))
        content = common.parseDOM(response.text, "div", attrs={"class": "b-content__inline_items"})

        items = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"})
        post_ids = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"}, ret="data-id")

        link_containers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-link"})

        links = common.parseDOM(link_containers, "a", ret='href')
        titles = common.parseDOM(link_containers, "a")
        div_covers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-cover"})

        country_years = common.parseDOM(link_containers, "div")

        for i, name in enumerate(titles):
            info = self.get_item_description(post_ids[i])
            title = "%s %s [COLOR=55FFFFFF](%s)[/COLOR]" % (name, color_rating(info['rating']), country_years[i])
            image = self._normalize_url(common.parseDOM(div_covers[i], "img", ret='src')[0])
            link = self.dom_protocol + "://" + links[i].split("://")[-1]
            uri = sys.argv[0] + '?mode=show&url=%s' % link
            year, country, genre = get_media_attributes(country_years[i])
            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            item.setInfo(
                type='video',
                infoLabels={
                    'title': title,
                    'genre': genre,
                    'year': year,
                    'country': country,
                    'plot': info['description'],
                    'rating': info['rating']
                }
            )
            is_serial = common.parseDOM(div_covers[i], 'span', attrs={"class": "info"})
            if (self.quality != 'select') and not is_serial:
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
            else:
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        if not len(titles) < 16:
            uri = sys.argv[0] + '?mode=%s&url=%s&page=%d' % ("index", url, page + 1)
            item = xbmcgui.ListItem("[COLOR=orange]" + self.language(1004) + "[/COLOR]", iconImage=self.inext)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def selectQuality(self, links, title, image, subtitles=None):
        lst = sorted(links.iteritems(), key=itemgetter(0))
        i = 0
        quality_prev = 360
        for quality, link in lst:
            i += 1
            if self.quality != 'select':
                if quality > int(self.quality[:-1]):
                    self.play(links[quality_prev], subtitles)
                    break
                elif len(lst) == i:
                    self.play(links[quality], subtitles)
            else:
                film_title = "%s (%s)" % (title, str(quality) + 'p')
                uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote(link)
                item = xbmcgui.ListItem(film_title, iconImage=image)
                item.setInfo(
                    type='Video',
                    infoLabels={'title': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0}
                )
                item.setProperty('IsPlayable', 'true')
                if subtitles:
                    item.setSubtitles([subtitles])
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
            quality_prev = quality

    def selectTranslator(self, content, post_id, url):
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
        ids = common.parseDOM(div, 'li', ret="data-translator_id")
        if len(titles) > 1:
            dialog = xbmcgui.Dialog()
            index_ = dialog.select(self.language(1006), titles)
            if int(index_) < 0:
                index_ = 0
        else:
            index_ = 0
        idt = ids[index_]

        data = {
            "id": post_id,
            "translator_id": idt
        }
        headers = {
            "Host": self.domain,
            "Origin": "http://" + self.domain,
            "Referer": url,
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest"
        }
        response = self.post_response(self.url + "/ajax/get_cdn_series/", data, headers).json()

        player = response["player"]
        seasons = response["seasons"]
        episodes = response["episodes"]
        iframe = common.parseDOM(player, 'iframe', ret='src')[0]
        playlist = common.parseDOM(episodes, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        return iframe, playlist

    def selectTranslator2(self, content):
        iframe0 = common.parseDOM(content, 'iframe', ret='src')[0]
        if self.translator != "select":
            return iframe0
        try:
            div = common.parseDOM(content, 'ul', attrs={'id': 'translators-list'})[0]
        except:
            return iframe0
        titles = common.parseDOM(div, 'li', ret="title")
        iframes = common.parseDOM(div, 'li', ret="data-cdn_url")
        if not iframes:
            return iframe0

        if len(titles) > 1:
            dialog = xbmcgui.Dialog()
            index_ = dialog.select(self.language(1006), titles)
            if int(index_) < 0:
                index_ = 0
        else:
            index_ = 0
        iframe = iframes[index_]

        return iframe

    def selectTranslator3(self, content, tvshow, post_id, url, idt, action):
        try:
            div = common.parseDOM(content, 'ul', attrs={'id': 'translators-list'})[0]
        except:
            return tvshow, idt, None
        titles = common.parseDOM(div, 'li', ret='title')
        ids = common.parseDOM(div, 'li', ret="data-translator_id")
        if len(titles) > 1:
            dialog = xbmcgui.Dialog()
            index_ = dialog.select(self.language(1006), titles)
            if int(index_) < 0:
                index_ = 0
        else:
            index_ = 0
        idt = ids[index_]

        data = {
            "id": post_id,
            "translator_id": idt,
            "action": action
        }
        is_director = common.parseDOM(div, 'li', attrs={'data-translator_id': idt}, ret='data-director')
        if is_director:
            data['is_director'] = is_director[0]

        headers = {
            "Host": self.domain,
            "Origin": "http://" + self.domain,
            "Referer": url,
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest"
        }

        #{"success":true,"message":"","url":"[360p]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/3dxox.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/61e68929526165ffb2e5483777a4bd94:2020101118\/8\/8\/1\/3\/3\/3dxox.mp4,[480p]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/ppjm0.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/6498b090482768d1433d456b2e35c46a:2020101118\/8\/8\/1\/3\/3\/ppjm0.mp4,[720p]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/0w0az.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/b10164963f454ad391b2a13460568561:2020101118\/8\/8\/1\/3\/3\/0w0az.mp4,[1080p]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/n9qju.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/b8a860d0938b593ed4b64723944b9a12:2020101118\/8\/8\/1\/3\/3\/n9qju.mp4,[1080p Ultra]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/4l9xx.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/13c067a1dcd54be75007a74bde421b17:2020101118\/8\/8\/1\/3\/3\/4l9xx.mp4","quality":"480p","subtitle":"[\u0420\u0443\u0441\u0441\u043a\u0438\u0439]https:\/\/static.voidboost.com\/view\/BmdZqxHeI9zXhhEWUUP70g\/1602429855\/8\/8\/1\/3\/3\/c1lz5sebdx.vtt,[\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430]https:\/\/static.voidboost.com\/view\/F8mGgsIZee6XMjvtXSojhQ\/1602429855\/8\/8\/1\/3\/3\/f0zfov3en4.vtt,[English]https:\/\/static.voidboost.com\/view\/enBDXHLd9y6OByIGY8AiZQ\/1602429855\/8\/8\/1\/3\/3\/ut8ik78tq5.vtt","subtitle_lns":{"off":"","\u0420\u0443\u0441\u0441\u043a\u0438\u0439":"ru","\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430":"ua","English":"en"},"subtitle_def":"ru","thumbnails":"\/ajax\/get_cdn_tiles\/0\/32362\/?t=1602170655"}

        response = self.post_response(self.url + "/ajax/get_cdn_series/", data, headers).json()

        subtitles = None
        if (action == "get_movie"):
            playlist = [response["url"] ]
            try:
                subtitles = response["subtitle"].split(']')[1].split(',')[0].replace("\/", "/")
            except:
                pass
        else:
            seasons = response["seasons"]
            episodes = response["episodes"]
            playlist = common.parseDOM(episodes, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        return playlist, idt, subtitles

    def getIFrame(self, content):
        return self.selectTranslator2(content)

    @staticmethod
    def get_links(data):
        log("*** get_links")
        links = data.replace("\/", "/").split(",")
        manifest_links = {}
        for link in links:
            if not ("Ultra" in link):
                manifest_links[int(link.split("]")[0].replace("[", "").replace("p", ""))] = link.split("]")[1]
            else:
                manifest_links[2160] = link.split("]")[1]
        return manifest_links

    def show(self, url):
        log("*** Show video %s" % url)
        response = self.get_response(url)

        content = common.parseDOM(response.text, "div", attrs={"class": "b-content__main"})[0]
        image = self.url + common.parseDOM(content, "img", attrs={"itemprop": "image"}, ret="src")[0]
        title = common.parseDOM(content, "h1")[0]
        post_id = common.parseDOM(content, "input", attrs={"id": "post_id"}, ret="value")[0]
        idt = "0"
        try:
           idt = common.parseDOM(content, "li", attrs={"class": "b-translator__item active"}, ret="data-translator_id")[0]
        except:
           try:
               idt = response.text.split("sof.tv.initCDNSeriesEvents")[-1].split("{")[0]
               idt = idt.split(",")[1].strip()
           except:
               pass
        subtitles = None
        tvshow = common.parseDOM(response.text, "div", attrs={"id": "simple-episodes-tabs"})
        if tvshow:
            if self.translator == "select":
                tvshow, idt, subtitles = self.selectTranslator3(content, tvshow, post_id, url, idt, "get_episodes")
            titles = common.parseDOM(tvshow, "li")
            ids = common.parseDOM(tvshow, "li", ret='data-id')
            seasons = common.parseDOM(tvshow, "li", ret='data-season_id')
            episodes = common.parseDOM(tvshow, "li", ret='data-episode_id')
            data = common.parseDOM(tvshow, "li", ret='data-cdn_url')

            for i, title_ in enumerate(titles):
                title_ = "%s (%s %s)" % (title_, self.language(1005), seasons[i])
                url_episode = url
                uri = sys.argv[0] + '?mode=play_episode&url=%s&urlm=%s&post_id=%s&season_id=%s&episode_id=%s&title=%s' \
                                    '&image=%s&idt=%s&data=%s' % (
                          url_episode, url, ids[i], seasons[i], episodes[i], title_, image, idt, data[i])
                item = xbmcgui.ListItem(title_, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title_})
                if self.quality != 'select':
                    item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True if self.quality == 'select' else False)
        else:
            content = [ response.text ]
            if (self.translator == "select"):
                content, idt, subtitles = self.selectTranslator3(content[0], content, post_id, url, idt, "get_movie")
            data = content[0].split('"streams":"')[-1].split('",')[0]

            links = self.get_links(data)
            self.selectQuality(links, title, image, subtitles)

        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def show_(self, url):
        log("*** Show video %s" % url)
        response = self.get_response(url)

        content = common.parseDOM(response.text, "div", attrs={"id": "wrapper"})
        image_container = common.parseDOM(content, "div", attrs={"class": "b-sidecover"})
        title = common.parseDOM(content, "h1")[0]
        image = common.parseDOM(image_container, "img", ret='src')[0]
        post_id = common.parseDOM(content, "input", attrs={"id": "post_id"}, ret="value")[0]

        playlist = common.parseDOM(content, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        iframe = self.getIFrame(content)
        if playlist:
            if self.translator == "select":
                iframe, playlist = self.selectTranslator(content, post_id, url)
            titles = common.parseDOM(playlist, "li")
            ids = common.parseDOM(playlist, "li", ret='data-id')
            seasons = common.parseDOM(playlist, "li", ret='data-season_id')
            episodes = common.parseDOM(playlist, "li", ret='data-episode_id')
            for i, title in enumerate(titles):
                title = "%s (%s %s)" % (title, self.language(1005), seasons[i])
                url_episode = iframe.split("?")[0]
                uri = sys.argv[0] + '?mode=play_episode&url=%s&urlm=%s&post_id=%s&season_id=%s&episode_id=%s&title=%s' \
                                    '&image=%s' % (
                          url_episode, url, ids[i], seasons[i], episodes[i], title, image)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title})
                if self.quality != 'select':
                    item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True if self.quality == 'select' else False)
        else:
            iframe = common.parseDOM(content, 'iframe', ret='src')[0]
            links, subtitles = self.get_video_link_from_iframe(iframe)
            self.selectQuality(links, title, image, subtitles)

        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def get_item_description(self, post_id):
        if self.description == "false":
            return {'rating': '', 'description': ''}
        data = {
            "id": post_id,
            "is_touch": 1
        }
        response = self.get_response(self.url + '/engine/ajax/quick_content.php', data)
        description = common.parseDOM(response.text, 'div', attrs={'class': 'b-content__bubble_text'})[0]

        try:
            imbd_rating = common.parseDOM(response.text, 'span', attrs={'class': 'imdb'})[0]
            rating = common.parseDOM(imbd_rating, 'b')[0]
        except IndexError as e:
            try:
                imbd_rating = common.parseDOM(response.text, 'span', attrs={'class': 'kp'})[0]
                rating = common.parseDOM(imbd_rating, 'b')[0]
            except IndexError as e:
                rating = 0
        return {'rating': rating, 'description': description}

    @staticmethod
    def get_video_link_from_iframe(url):
        log("*** get_video_link_from_iframe")
        headers = {
            "User-Agent": USER_AGENT,
            "Referer": "http://www.random.org"
        }
        request = urllib2.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        if "var embed_player =" in response:
            url = response.split("var embed_player = '<iframe src=\"")[-1].split('"')[0]
            request = urllib2.Request(url, "", headers)
            request.get_method = lambda: 'GET'
            response = urllib2.urlopen(request).read()

        subtitles = None
        if 'subtitles: {"master_vtt":"' in response:
            subtitles = response.split('subtitles: {"master_vtt":"')[-1].split('"')[0]

        ###################################################
        values, attrs = moonwalk.get_access_attrs(response, url)
        ###################################################

        headers = {}
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        opener.addheaders = [("User-Agent", USER_AGENT)]
        request = urllib2.Request(attrs["purl"], urllib.urlencode(values), headers)
        connection = opener.open(request)
        response = connection.read()
        data = json.loads(response.decode('unicode-escape'))
        playlisturl = data["m3u8"]

        headers = {
            "Host": PLAYLIST_DOMAIN,
            "Referer": url,
            "Origin": "http://" + PLAYLIST_DOMAIN,
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest"
        }

        request = urllib2.Request(playlisturl, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()

        urls = re.compile(r"http:\/\/.*?\n").findall(response)
        manifest_links = {}
        for i, url in enumerate(urls):
            manifest_links[QUALITY_TYPES[i]] = url.replace("\n", "")

        return manifest_links, subtitles

    def get_seasons_link(self, referer, video_id, season, episode):
        log('*** get_seasons_link')
        data = {
            'id': video_id,
            'season': season,
            'episode': episode
        }
        response = self.get_response(self.url + '/engine/ajax/getvideo.php', data, referer=referer).json()
        return response['link']['hls']

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
        kbd.setHeading(self.language(1000))
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            if self.addon.getSetting('translit') == 'true':
                keyword = transliterate.rus(kbd.getText())
            else:
                keyword = kbd.getText()

            history.add_to_history(keyword)

        return keyword

    def search(self, keyword, external):
        log("*** search")
        keyword = urllib.unquote_plus(keyword) if (external is not None) else self.getUserInput()

        if keyword:
            data = {
                "do": "search",
                "subaction": "search",
                "q": unicode(keyword)
            }
            response = self.get_response(self.url + "/search/", data, cookies={"dle_user_taken": "1"})

            content = common.parseDOM(response.text, "div", attrs={"class": "b-content__inline_items"})
            items = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"})
            post_ids = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"}, ret="data-id")
            link_containers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-link"})
            links = common.parseDOM(link_containers, "a", ret='href')
            titles = common.parseDOM(link_containers, "a")
            country_years = common.parseDOM(link_containers, "div")

            for i, name in enumerate(titles):
                info = self.get_item_description(post_ids[i])
                title = "%s %s [COLOR=55FFFFFF](%s)[/COLOR]" % (name, color_rating(info['rating']), country_years[i])
                image = self._normalize_url(common.parseDOM(items[i], "img", ret='src')[0])
                link = self.dom_protocol + "://" + links[i].split("://")[-1]
                uri = sys.argv[0] + '?mode=show&url=%s' % link
                year, country, genre = get_media_attributes(country_years[i])
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(
                    type='video',
                    infoLabels={
                        'title': title,
                        'genre': genre,
                        'year': year,
                        'country': country,
                        'plot': info['description'],
                        'rating': info['rating']
                    }
                )
                is_serial = common.parseDOM(items[i], 'span', attrs={"class": "info"})
                if (self.quality != 'select') and not is_serial:
                    item.setProperty('IsPlayable', 'true')
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
                else:
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            xbmcplugin.setContent(self.handle, 'movies')
            xbmcplugin.endOfDirectory(self.handle, True)
        else:
            self.menu()

    def play(self, url, subtitles=None):
        log('*** play')
        item = xbmcgui.ListItem(path=url)
        if subtitles:
            item.setSubtitles([subtitles])
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def play_episode(self, url, referer, post_id, season_id, episode_id, title, image, idt, data):
        log("*** play_episode")
        if (data == "null"):
            data = {
                "id": post_id,
                "translator_id": idt,
                "season": season_id,
                "episode": episode_id,
                "action": "get_stream"
            }
            headers = {
                "Host": self.domain,
                "Origin": "http://" + self.domain,
                "Referer": url,
                "User-Agent": USER_AGENT,
                "X-Requested-With": "XMLHttpRequest"
            }
            response = self.post_response(self.url + "/ajax/get_cdn_series/", data, headers).json()
            data = response["url"]
        links = self.get_links(data)
        self.selectQuality(links, title, image, None)
        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def play_episode_(self, url, referer, post_id, season_id, episode_id, title, image):
        log("*** play_episode")
        try:
            url = self.get_seasons_link(referer, post_id, season_id, episode_id)

            item = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(self.handle, True, item)

        except Exception as ex:
            url_episode = url + "?nocontrols=1&season=%s&episode=%s" % (season_id, episode_id)
            links, subtitles = self.get_video_link_from_iframe(url_episode)
            self.selectQuality(links, title, image, subtitles)
            xbmcplugin.setContent(self.handle, 'episodes')
            xbmcplugin.endOfDirectory(self.handle, True)

    def _normalize_url(self, item):
        if not item.startswith("http"):
            item = self.url + item
        return item

    def showMessage(self, msg):
        log(msg)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("Info", msg, str(5 * 1000)))

    def showErrorMessage(self, msg):
        log(msg)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))


def get_media_attributes(source):
    items = source.split(',')
    if len(items) == 3:
        year, country, genre = items
    else:
        year, genre = items
        country = 'Unknown'
    return year, country, genre


def color_rating(rating):
    if not rating:
        return ''
    rating = float(rating)
    if 0 <= rating < 5:
        return '[COLOR=red][%s][/COLOR]' % rating
    elif 5 <= rating < 7:
        return '[COLOR=yellow][%s][/COLOR]' % rating
    elif rating >= 7:
        return '[COLOR=green][%s][/COLOR]' % rating


def log(msg, level=xbmc.LOGNOTICE):
    log_message = u'{0}: {1}'.format('hdrezka', msg)
    xbmc.log(log_message.encode("utf-8"), level)


plugin = HdrezkaTV()
plugin.main()

#sof.tv.initCDNSeriesEvents(1826, 13, 1, 1, false, 'rezka.ag', false, {
