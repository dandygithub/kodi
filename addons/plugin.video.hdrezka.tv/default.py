#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Writer (c) 2012-2019, MrStealplugindandy
# Rev. 2.3.0

import json
import os
import re
import socket
import sys
import urllib
from operator import itemgetter
import base64

import XbmcHelpers
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import SearchHistory as history

from constants import *
from common import *
from search import *
from qualityAndTranslator import *
from pluginSettings import *
from itertools import chain, product
common = XbmcHelpers

socket.setdefaulttimeout(120)


class HdrezkaTV:
    def __init__(self):
        self.addon = xbmcaddon.Addon(PluginId)
        self.icon = self.addon.getAddonInfo('icon')

        self.language = getLanguageSettings()
        self.inext = os.path.join(self.addon.getAddonInfo('path'), 'resources/icons/next.png')
        self.handle = getHandleSettings()
        self.dom_protocol = getDomProtocolSettings()
        self.domain = getDomainSettings()
        self.url = getUrlSettings()
        self.proxies = getProxySettings()
        self.quality = getQualitySettings()
        self.translator = getTranslatorSettings()
        self.description = getDescriptionSettings()

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
            search(self, params.get('keyword'), external)
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
        response = get_response(self.url)
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
        response = get_response(url)
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

        response = get_response(self.url + page_url)
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
        response = get_response("%s/page/%s/" % (url, page))
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

    def get_item_description(self, post_id):
        if self.description == "false":
            return {'rating': '', 'description': ''}
        data = {
            "id": post_id,
            "is_touch": 1
        }
        response = get_response(self.url + '/engine/ajax/quick_content.php', data)
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
    def decode_trash(str,removelist):
        n=4
        cleanedsubstring = str
        y=0
        while y < len(str):
            chunk = str[y:y+n]
            if chunk in removelist:
                cleanedsubstring = cleanedsubstring.replace(chunk,'',1)
            else:            
                break
            y += n
        return cleanedsubstring
    
    def decode_clean_list(self,decList,removelist):
        i=0
        list_lenght = len(decList)
        list_cleaned = []
        while list_lenght>i:
            currentsubstring = decList[list_lenght-1]
            list_cleaned.insert(0,self.decode_trash(currentsubstring,removelist))
            list_lenght -= 1
        return list_cleaned
    
    def decode_response(self,r):
        
        r_decoded = ''
        #--Generate trash codes-- start#
        trashCodesSet = set()
        trashList = ["@","#","!","^","$"]
        for i in range(2,4):
            startchar = ''
            for chars in product(trashList, repeat=i):
                trashcombo = base64.b64encode(startchar.join(chars))
                trashCodesSet.add(trashcombo)
        #--Generate trash codes -- finish#
        #--Clean 1st step       -- start#
        templist = self.decode_clean_list( list( re.split(r'_', re.sub(r'(\/|\\)','',r)) )  ,trashCodesSet)
        #--Clean 1st step       -- finish#
        #--Result preparing      -- start#
        start_from_position = len(templist)
        output = ''
        while start_from_position !=1 :
            itemString = templist[start_from_position-2] + templist[start_from_position-1]
            output = self.decode_trash(itemString,trashCodesSet)
            del templist[-1]
            del templist[-1]
            templist.append(output)
            start_from_position = len(templist)
        r_decoded = base64.b64decode(''.join(templist).replace('#h','',1))
        #--Result preparing      -- finish#
        return r_decoded
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
        
    @staticmethod
    def get_subtitles(response):
        subtitles = None
        try:
            subtitles = response["subtitle"].split(',')
            for si in range(len(subtitles)):
                subtitles[si] = subtitles[si].split(']')[1].replace("\/", "/")
        except:
            pass

        return subtitles
    
    @staticmethod    
    def set_item_subtitles(item, subtitles):
        if subtitles:
            if not isinstance(subtitles, list):
                subtitles = [ subtitles ]
                
            item.setSubtitles(subtitles)
        
    def show(self, url):
        log("*** Show video %s" % url)
        response = get_response(url)

        content = common.parseDOM(response.text, "div", attrs={"class": "b-content__main"})[0]
        image = common.parseDOM(content, "img", attrs={"itemprop": "image"}, ret="src")[0]
        log("*** Show video image %s" % image)
        mainTitle = common.parseDOM(content, "h1")[0]
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
                tvshow, idt, subtitles = selectTranslator3(self, content, tvshow, post_id, url, idt, "get_episodes")
            titles = common.parseDOM(tvshow, "li")
            ids = common.parseDOM(tvshow, "li", ret='data-id')
            seasons = common.parseDOM(tvshow, "li", ret='data-season_id')
            episodes = common.parseDOM(tvshow, "li", ret='data-episode_id')
            data = common.parseDOM(tvshow, "li", ret='data-cdn_url')

            for i, title_ in enumerate(titles):
                title_ = "%s (S%sE%s)" % (mainTitle, seasons[i], episodes[i])
                url_episode = url
                uri = sys.argv[0] + '?mode=play_episode&url=%s&urlm=%s&post_id=%s&season_id=%s&episode_id=%s&title=%s' \
                                    '&image=%s&idt=%s&data=%s' % (
                          url_episode, url, ids[i], seasons[i], episodes[i], title_, image, idt, data[i])
                item = xbmcgui.ListItem(title_, iconImage=image, thumbnailImage=image)
                item.setInfo(
                    type='video', 
                    infoLabels={
                        'plot': mainTitle
                        })
                if self.quality != 'select':
                    item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True if self.quality == 'select' else False)
        else:
            content = [ response.text ]
            if (self.translator == "select"):
                content, idt, subtitles = selectTranslator3(self, content[0], content, post_id, url, idt, "get_movie")
            data = content[0].split('"streams":"')[-1].split('",')[0]

            links = self.get_links(self.decode_response(data))
            selectQuality(self, links, mainTitle, image, subtitles)

        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def history(self):
        words = history.get_history()
        for word in reversed(words):
            uri = sys.argv[0] + '?mode=%s&keyword=%s&main=1' % ("search", word)
            item = xbmcgui.ListItem(word, iconImage=self.icon, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        xbmcplugin.endOfDirectory(self.handle, True)

    def play(self, url, subtitles=None):
        log('*** play')
        item = xbmcgui.ListItem(path=url)
        self.set_item_subtitles(item, subtitles)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def play_episode(self, url, referer, post_id, season_id, episode_id, title, image, idt, data):
        log("*** play_episode")
        subtitles = None
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
            response = post_response(self.url + "/ajax/get_cdn_series/", data, headers).json()
            data = response["url"]
            subtitles = self.get_subtitles(response)
        links = self.get_links(self.decode_response(data))
        selectQuality(self, links, title, image, subtitles)
        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def _normalize_url(self, item):
        if not item.startswith("http"):
            item = self.url + item
        return item

plugin = HdrezkaTV()
plugin.main()

#sof.tv.initCDNSeriesEvents(1826, 13, 1, 1, false, 'rezka.ag', false, {
