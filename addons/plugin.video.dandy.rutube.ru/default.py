#!/usr/bin/python
# -*- coding: utf-8 -*-
# Writer (c) 2014-2017, dandy, MrStealth
# Rev. 1.0.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import urllib
import urllib2
import sys
import socket
import json
import re

from urllib2 import Request, build_opener, HTTPCookieProcessor, HTTPHandler
import cookielib

from StringIO import StringIO
import gzip

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import XbmcHelpers
common = XbmcHelpers

import Translit as translit
translit = translit.Translit()

#import SearchHistory

try:
    sys.path.append(os.path.dirname(__file__)+ '/../plugin.video.unified.search')
    from unified_search import UnifiedSearch
except:
    pass 

import xml.etree.ElementTree

socket.setdefaulttimeout(120)

#const
SELECTED_GROUPS = (0, 1)
SELECTED_MAIN_TABS = (0, 1)
QUALITY_TYPES = (("lq", 0, 1000000), ("mq", 1000001, 1500000), ("hq", 1500001, 2000000), ("hd", 2000001, 99999999))

#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1, BANDWIDTH=698000, CODECS="avc1.42c015, mp4a.40.5"
#http://video-1-101.rutube.ru/hls-vod/XIlMXrdnc_4u_tybeCnWSw/1489590308/122/0x500003970be00fb4/265a274360dd40ecb5579ced68d7580a.mp4.m3u8?i=512x288_698
#EXT-X-STREAM-INF:PROGRAM-ID=1, BANDWIDTH=1299000, CODECS="avc1.4d401e, mp4a.40.5"
#http://video-1-101.rutube.ru/hls-vod/HT87paLmteEyCprimFUCwA/1489590308/124/0x500003970b8829c4/6bb45bffe33b4308b45fd2932236cbff.mp4.m3u8?i=640x360_1299
#EXT-X-STREAM-INF:PROGRAM-ID=1, BANDWIDTH=1997000, CODECS="avc1.4d401f, mp4a.40.5"
#http://video-1-101.rutube.ru/hls-vod/EaDpUG1QPo_mQMxbhw9Mvw/1489590308/124/0x500003970b90123b/ec392beb7200457aab7e434811911c7d.mp4.m3u8?i=896x504_1997
#EXT-X-STREAM-INF:PROGRAM-ID=1, BANDWIDTH=3591000, CODECS="avc1.64001f, mp4a.40.5"
#http://video-1-101.rutube.ru/hls-vod/f0x5PZRgROGZUppis5_a8g/1489590308/122/0x500003970bd81942/f828922310e745fd80da425193db2dec.mp4.m3u8?i=1280x720_3591

class RuTube():

    def __init__(self):
        self.id = "plugin.video.dandy.rutube.ru"
        self.addon = xbmcaddon.Addon(self.id)
        self.path = self.addon.getAddonInfo('path')
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.profile = self.addon.getAddonInfo('profile')
        self.version = self.addon.getAddonInfo('version')

        self.language = self.addon.getLocalizedString

        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.url = 'https://rutube.ru'

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.debug = False

        self.quality = self.addon.getSetting('quality')
        if not self.quality:
            self.quality = 'auto'

        self.prev = ''
        self.categorie = ''

        self.cat_images={'rentv': 'https://pic.rutube.ru/promoitem/cb/36/cb3643a5b5d43d0264574145cec7484e.jpg', 
                         'tnt': 'https://pic.rutube.ru/promoitem/a1/a4/a1a45ae753a74e69dd6d35adec7cb564.jpg', 
                         'stb': 'https://pic.rutube.ru/promoitem/48/ce/48ceaa6d7d240976de0bb4fad5cf2ba0.jpg', 
                         'russia1': 'https://pic.rutube.ru/promoitem/2b/e8/2be84151b2bbc6de82d49f40c212645a.jpg', 
                         'friday': 'https://pic.rutube.ru/promoitem/c4/72/c47249c0882849b2c506c2335d554f3a.jpg', 
                         'tv3': 'https://pic.rutube.ru/promoitem/e2/a5/e2a5f013620911a4cf4aeea2726ef932.jpg', 
                         'russia24': 'https://pic.rutube.ru/promoitem/c4/2a/c42a1791fe56bc2892b4cfb2a5844721.jpg', 
                         'ctc': 'https://pic.rutube.ru/promoitem/bd/77/bd77392fe6709705f362df68ceb6cec2.jpg', 
                         '2x2': u'https://pic.rutube.ru/promoitem/51/1f/511f2c50aae28cd5a55bd5a158c3904f.jpg', 
                         'redmedia/': 'https://pic.rutube.ru/promoitem/e6/fb/e6fbe78342ead9d64a89355659b50223.jpg',

                         'serials': 'https://pic.rutube.ru/promoitem/bb/90/bb9060f129ee20088ba0abf2c91aa81b.png', 
                         'eda': 'https://pic.rutube.ru/promoitem/f4/9e/f49ea030da839708138d21c16c8e38bc.jpg', 
                         'bloggers': 'https://pic.rutube.ru/promoitem/18/60/1860aa0ffb69614a37f07acfcaabcde8.jpg', 
                         'tv': 'https://pic.rutube.ru/promoitem/8f/c3/8fc3f7d64fe67123f3133ec7cb11acbd.png', 
                         'auto': 'https://pic.rutube.ru/promoitem/a1/34/a134fc7538bc8a4cbe1910da9d2726d2.jpg', 
                         'travel': 'https://pic.rutube.ru/promoitem/7d/02/7d02655e58f9953127100a4c904fea7d.jpg', 
                         'hitech': 'https://pic.rutube.ru/promoitem/68/3f/683f55883b22de46a39524c3ed3dc3f4.jpg', 
                         'movies': 'https://pic.rutube.ru/promoitem/11/fc/11fc86e0114024cd94a30d077ddc8b47.png', 
                         'dances': 'https://pic.rutube.ru/promoitem/cb/60/cb60e0e014bd9d7266cebdab90d2545b.jpg', 
                         'kids': 'https://pic.rutube.ru/promoitem/89/b9/89b9d15b7e094b9a753edc25d1d428c7.jpg', 
                         'games': 'https://pic.rutube.ru/promoitem/64/7e/647ecd9068f27bc2d32383acd954f6e7.jpg', 
                         'anime': 'https://pic.rutube.ru/promoitem/e2/c9/e2c90474564525639a0154486ed707ac.jpg', 
                         'news': 'https://pic.rutube.ru/promoitem/b4/db/b4dbd994dbc77371c9ac8d6970fd82b8.png', 
                         'fun': 'https://pic.rutube.ru/promoitem/8d/55/8d5587260f9ec3d30b21fd57ebce3346.jpg', 
                         'music': 'https://pic.rutube.ru/promoitem/b6/c8/b6c8590be670e14e3f14ba9aeb0ace14.png', 
                         'sport': 'https://pic.rutube.ru/promoitem/8e/1b/8e1bb3b5642e5411269e427f40b0160b.png'}

    def main(self):
        self.log("Addon: %s"  % self.id)
        self.log("Handle: %d" % self.handle)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)
        mode = params['mode'] if 'mode' in params else None
        url = UQT(params['url'].replace('\"', '')) if 'url' in params else None
        image = UQT(params['image'].replace('\"', '')) if 'image' in params else None        

        keyword = params['keyword'] if 'keyword' in params else None
        external = 'unified' if 'unified' in params else None
        if external == None:
            external = 'usearch' if 'usearch' in params else None    
        page = int(params['page']) if 'page' in params else 1

        group = int(params['group']) if 'group' in params else None
        name = params['name'] if 'name' in params else ''

        self.categorie = params['categorie'] if 'categorie' in params else self.categorie
        self.prev = params['prev'] if 'prev' in params else ''

        tab = int(params['tab']) if 'tab' in params else 0

        lock = params['lock'] if 'lock' in params else '0'
 
        if mode == 'search':
            self.search(keyword, external, page)
        elif mode == 'group':
            self.getGroupItemsNew(group)
        elif mode == 'tabs':
            self.tabs(url)
        elif mode == 'subtabs':
            self.subTabsNew(url, image)
        elif mode == 'list':
            self.getListNew(url, page)
        elif mode == 'show':
            self.show(url)
        elif mode == 'play':
            self.play(url, name, lock)
        else:
            self.mainMenu()

    def mainMenu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(1000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

	self.items(self.url, True)

    def items(self, url, main = False):
        self.log("-items:")
        ct_cat = []
        
        response = self.get_url(url)
        jdata = re.compile("window.applicationState = {(.*?)};").findall(response)[0].replace("\\x3d", "=").replace("\\x26", "&").replace("\\x3e", ">").replace("\\x3c", "<")
        js = json.loads('{'+jdata+'}')
        jspart = js["sideNavStore"]["links"]["profile_woodpecker"][0]
        for i, item in enumerate(jspart["links"]):
            if (not main) or (i in SELECTED_MAIN_TABS):
                name = item["name"]
                url = self.url + item["link"]
                params = '?mode=list&url=' + QT(url)
                ct_cat.append((params, self.icon, True, {'title': name}))

        jspart = js["sideNavStore"]["links"]["catalog_woodpecker"]
        for i, item in enumerate(jspart):
            if main and (i in SELECTED_GROUPS):
                name = "[COLOR=orange]" + item["name"] + "[/COLOR]"
                params = '?mode=group&group=' + str(i)
                ct_cat.append((params, self.icon, True, {'title': name}))

        self.listItems(ct_cat, True)


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

    def search(self, keyword, external, page = 1):
        if page == 1:
            keyword = keyword if (external != None) or keyword else self.getUserInput()
            if keyword:
                keyword = translit.rus(keyword) if (external == 'unified') else urllib.unquote_plus(keyword)
        else:
            keyword = urllib.unquote_plus(keyword)

        unified_search_results = []

        if keyword:
            url = "https://rutube.ru/api/search/video/"

            values = {
                "order_by": "rank",
                "duration": "",
                "created": "",
                "only_hd": "false",
                "no_adult": "false",
                "query": encode2(keyword),
                "page": str(page),
                "perPage": "10"
            }

            headers = {
                "Host": "rutube.ru",
                "Connection": "keep-alive",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "X-Ally": "1",
                "X-CSRFToken": "4qb8a9ysuvpxudljpz3o6ngljciy8pl2",
                "Referer": "https://rutube.ru/search/?query=" + encode2(keyword),
                "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4",
            }

            form = urllib.urlencode(values)
            encoded_kwargs = urllib.urlencode(values.items())
            argStr = "?%s" %(encoded_kwargs)
            request = urllib2.Request(url + argStr, "", headers)
            request.get_method = lambda: 'GET'
            response = urllib2.urlopen(request)
            data = json.loads(response.read())

            for i, result in enumerate(data['results']):
                image = result['thumbnail_url']
                if (external == 'unified'):
                    unified_search_results.append({'title': result['title'], 'url': 'https://rutube.ru/video/%s/?ref=search' % result['id'], 'image': image, 'plugin': self.id})
                else:  
                    uri = sys.argv[0] + '?mode=play&url=https://rutube.ru/video/%s/?ref=search' % result['id']
                    item = xbmcgui.ListItem(result['title'], iconImage=image, thumbnailImage=image)
                    item.setProperty('IsPlayable', 'true')
                    item.setInfo(type='Video', infoLabels={'title': result['title']})
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

            if (external == None) and (data['has_next'] == True):
                uri = sys.argv[0] + '?mode=%s&keyword=%s&page=%s' % ('search', keyword, str(page + 1))
                item = xbmcgui.ListItem('[COLOR=FFFFD700]' + self.language(2000) % (str(page+1)) + '[/COLOR]', thumbnailImage=self.inext, iconImage=self.inext)
                item.setInfo(type='Video', infoLabels={'title': '<NEXT PAGE>'})
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if (external == 'unified'):
                UnifiedSearch().collect(unified_search_results)
            else: 
                xbmcplugin.setContent(self.handle, 'movies')
                xbmcplugin.endOfDirectory(self.handle, True)

    def getGroups(self):
        response = common.fetchPage({"link": self.url})
        content = response["content"].split('<div class="sub-header">')[-1].split('</body>')[0]
        groups = common.parseDOM(content, "div", attrs={"class": "sub-header-row-left-inner"})
        for i, group in enumerate(groups):
            if i in SELECTED_GROUPS:
                uri = sys.argv[0] + '?mode=group&group=%s' % (str(i))
                item = xbmcgui.ListItem("[COLOR=FF7B68EE]%s[/COLOR]" % group, iconImage=self.icon, thumbnailImage=self.icon)
                item.setInfo(type='Video', infoLabels={'title': group})
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

    def getCategorieImage(self, icon, url, categorie, load = True):
        if icon:
            return icon
        else:
            if (categorie in self.cat_images):
                return self.cat_images[categorie]
            else:
                if load == True:    
                    response = common.fetchPage({"link": url})
                    content = response["content"]
                    block = common.parseDOM(content, "script", attrs={"class": "initial-data"})[0]
                    image = '' 
                    if "picture:" in block:
                        image = block.split("picture:")[1].split(";")[0]
                    if not ("https://" in image):
                        image = self.icon
                    else:
                        self.cat_images[categorie] = image
                else:
                    image = self.icon      
                return image 

    def getCategorie(self, data, categorie):
        if '/feeds/' in data:
            return data.split('/feeds/')[-1].split('/')[0]
        else:
            return categorie

    def getGroupItemsNew(self, group):
        self.log("-groupItems:")
        ct_cat = []
        response = self.get_url(self.url)
        jdata = re.compile("window.applicationState = {(.*?)};").findall(response)[0].replace("\\x3d", "=").replace("\\x26", "&").replace("\\x3e", ">").replace("\\x3c", "<")

        js = json.loads('{'+jdata+'}')
        jspart = js["sideNavStore"]["links"]["catalog_woodpecker"]
        for i, item_group in enumerate(jspart):
       	    if (i == group):
                for j, item in enumerate(item_group["links"]):
                    name = item["name"]
                    url = self.url + item["link"]
                    params = '?mode=subtabs&url="' + QT(url) + '"'
                    ct_cat.append((params, self.icon, True, {'title': html_unescape(name)}))
                break
        self.listItems(ct_cat, True)

    def getGroupItems(self, group):
        response = common.fetchPage({"link": self.url})
        content = response["content"].split('<div class="sub-header">')[-1].split('</body>')[0]
        groupitems = common.parseDOM(content, "div", attrs={"class": "sub-header-row-right"})[group]

        titles = common.parseDOM(groupitems, "a", attrs={"class": "sub-header-row-list-link "})
        urls   = common.parseDOM(groupitems, "a", attrs={"class": "sub-header-row-list-link "}, ret="href")
                
        for i, title in enumerate(titles):
            categorie = self.getCategorie(urls[i], self.categorie)
            uri = sys.argv[0] + '?mode=tabs&url=%s&categorie=%s' % (self.url + urls[i], categorie)
            image = self.getCategorieImage(self.url + urls[i], categorie) 
            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            item.setInfo(type='Video', infoLabels={'title': title})
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def listItems(self, ictlg, films=False):
        self.log("-listItems:")
        
        for ctUrl, ctIcon, ctFolder, ctLabels in ictlg:
            ctTitle = ctLabels['title']
            item = xbmcgui.ListItem(ctTitle, iconImage=ctIcon, thumbnailImage=ctIcon)
            item.setInfo(type='Video', infoLabels=ctLabels)
            if ctFolder == False: item.setProperty('IsPlayable', 'true')
            item.setProperty('fanart_image', self.fanart)
            xbmcplugin.addDirectoryItem(self.handle, ("" if ctUrl == "*" else sys.argv[0] + ctUrl), item, ctFolder)
            self.log("ctTitle: %s"  % ctTitle) 
            self.log("ctIcon: %s"  % ctIcon) 

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle)

    def tabs(self, url, main = False):
        self.log("-tabs:")
        ct_cat = []
        
        response = self.get_url(url)
        jdata = re.compile("initialData.showcase = '{(.*?)}';").findall(response)[0].decode('unicode-escape')
        js = json.loads('{'+jdata+'}')
        for i, tab in enumerate(js['tabs']):
            if (not main) or (i in SELECTED_MAIN_TABS):
                name = tab['name']
                url = tab['url']
                params = '?mode=subtabs&url=' + QT(url)
                if '/feeds/' + self.categorie + '/popular/' not in url:
                    ct_cat.append((params, self.getCategorieImage(url, self.getCategorie(url, self.categorie), False), True, {'title': name}))
        self.listItems(ct_cat, True)

    def subTabs(self, url):
        self.log("-subTabs:")
        self.log("--url: %s"%url)
        ct_list = []

        response = common.fetchPage({"link": url})
        content = response["content"]
        subtabs = common.parseDOM(content, "span", attrs={"class": "showcase-widget-name-text"})
        titles = common.parseDOM(container, "a")
        urls = common.parseDOM(container, "a", ret="href")

        if (len(subtabs) == 0):
            self.getListNew(url) 
        else:        
            for i, subtab in enumerate(titles):
                params = '?mode=list&url=%s&tab=%s'%(QT(self.url + urls[i]), str(i))
                ct_list.append((params, self.getCategorieImage(url, self.getCategorie(url, self.categorie), False), True, {'title': name}))

            self.listItems(ct_list, True)

    def subTabsNew(self, url, image=None):
        self.log("-subTabs:")
        self.log("--url: %s"%url)
        ct_list = []

        response = self.get_url(url.replace('\"', ''))
        container = common.parseDOM(response, "nav", attrs={"class": "showcase-tabs"})
        titles = common.parseDOM(container, "a")
        urls = common.parseDOM(container, "a", ret="href")

        if (len(titles) == 0):
            self.getListNew(url) 
        else:        
            for i, title in enumerate(titles):
                params = '?mode=list&url=%s&tab=%s'%(QT(self.url + urls[i]), str(i))
                ct_list.append((params, image if image else self.icon, True, {'title': html_unescape(title)}))

            self.listItems(ct_list, True)

    def getList(self, url, tab = 0):
        self.log("-getList:")
        self.log("--url: %s"%url)
        ct_list = []
        
        response = self.get_url(url)
        
        if self.prev == 'list':
            jts = make_dict_from_tree(xml.etree.ElementTree.fromstring(response))['root']
            results = jts['results']['list-item']
        else: 
            jtdata = re.compile("initialData.resultsOfActiveTabResources\[(.*?)\] = '{(.*?)}';").findall(response)[tab][1].decode('unicode-escape')
            jts = json.loads('{'+jtdata+'}')
            results = jts['results']

        for res in results:
            name = ''
            url = ''
            pic = ''
            plot = ''
            try:
                name = res['object']['name']
                pic = res['object']['picture']
                url = res['object']['absolute_url']
                plot = res['object']['description']
            except:
                try:
                    name = res['title']
                    pic = res['picture_url']
                    url = res['video_url']
                    plot = res['description']
                except: 
                    try:
                        name = res['title']
                        pic = res['picture']
                        url = self.url + res['target']
                        plot = res['description']

                    except:
                        try:
                            name = res['video']['title']
                            pic = res['video']['thumbnail_url']
                            url = res['video']['video_url']
                            plot = res['video']['description']
                        except: pass
    
            if pic == '' or pic == None:
                try: pic = res['thumbnail_url']
                except: pass
            if plot == '' or plot == None:
                try: plot = res['short_description']
                except: pass
                
            self.log("-m_list-name: %s"%name)
            self.log("-m_list-pic: %s"%pic)
            self.log("-m_list-url: %s"%url)

            if url and name:
                if (url.find('rutube.ru/video') > -1 or url.find('play/embed') > -1) and url.find('person') < 0 :
                    mode = 'play&name=%s&icon=%s&prev=list'%(name, QT(pic))
                    folder = False
                else:
                    mode = 'show'
                    folder = True
                params = '?mode=%s&url=%s'%(mode, QT(url))
                ct_list.append((params, pic, folder, {'title': name, 'plot':plot}))

        try: next = str(jts['has_next']).capitalize()
        except: next = ''
            
        if next == 'True':
            params = '?mode=%s&prev=list&url=%s&tab=%s'%('list', QT(jts['next']), str(tab))
            ct_list.append((params, self.inext, True, {'title': '[COLOR=FFFFD700]' + self.language(2001) + '[/COLOR]'}))
        
        self.listItems(ct_list, True)

    def getListNew_(self, container, ct_list):
        name = common.parseDOM(container, "h3", attrs={"class": "widget-header__name"})
        if name:
            name = common.stripTags(name[0])
            params = "*"
            ct_list.append((params, self.icon, False, {"title": "[COLOR=orange]" + html_unescape(name) + "[/COLOR]"}))

        articles = common.parseDOM(container, "article")
        contents = common.parseDOM(articles, "div", attrs={"class": "element-cover__content"})
        titles = common.parseDOM(contents, "a", attrs={"class": "element-cover__link"}, ret="title")
        urls = common.parseDOM(contents, "a", attrs={"class": "element-cover__link"}, ret="href")

        if (len(titles) > 0):
            for i, item in enumerate(titles):
                lock = "1" if common.parseDOM(contents[i], "button", attrs={"class": "element-cover__club-lock"}) else "0"
                params = "?mode=play&url=%s&lock=%s"%(QT(self.url + urls[i]), lock)
                if (lock == "1"):
                    item = "[COLOR=red]" + item + "[/COLOR]"
                imagel = common.parseDOM(articles[i], "img", ret="src")
                if (not imagel):
	                imagel = common.parseDOM(articles[i], "div", attrs={"class": "element-cover__img"}, ret="style")
                if (not imagel):
	                imagel = common.parseDOM(articles[i], "div", attrs={"class": "element-cover__img element-cover__img_is-adult element-cover__img_covered"}, ret="style")
                image = (imagel[0] if (imagel) else self.icon)
                if ("background-image:" in image):
                    image = image.split('background-image:url(')[-1].split(')')[0]
                ct_list.append((params, image, False, {"title": html_unescape(item)}))
        else:
            titles = common.parseDOM(articles, "a", ret="title")
            urls = common.parseDOM(articles, "a", ret="href")

            for i, item in enumerate(titles):
                image = common.parseDOM(articles[i], "div", attrs={"class": "cardgroup-card__picture"}, ret="style")[0]
                image = (image if (image) else self.icon)
                if ("background-image:" in image):
                    image = image.split('background-image:url(')[-1].split('?')[0]
                params = "?mode=subtabs&url=%s&image=%s"%(QT(self.url + urls[i]), QT(image))
                ct_list.append((params, image, True, {"title": html_unescape(item)}))

    def getListNew(self, url, page = 1):
        self.log("-getList:")
        self.log("--url: %s"%url)
        ct_list = []

        response = self.get_url(url.replace('\"', '') +  ("" if (page == 1) else (("&" if  ("?" in url) else "?") + "page=" + str(page))))

        main = common.parseDOM(response, "main", attrs={"class": "showcase"})
        if (not main):
            main = response
        else:    
            main = main[0]    
        containers = common.parseDOM(main, "div", attrs={"class": "layout-container"})
        if containers:
            for container in containers:
                self.getListNew_(container, ct_list)
        if (len(ct_list) == 0):
            container = common.parseDOM(main, "div", attrs={"class": "grid-widget"})
            if container:
                self.getListNew_(container[0], ct_list)

        next = common.parseDOM(response, "link", attrs={"rel": "next"})
        if next:
            params = "?mode=list&url=%s&page=%s"%(QT(url), str(page+1))
            ct_list.append((params, self.inext, True, {"title": "[COLOR=lightgreen]" + self.language(2000) % (str(page+1)) + "[/COLOR]"}))
        
        self.listItems(ct_list, True)

        
    def show(self, url):
        self.log("-show:")
        self.log("--url: %s" % url)
        ct_show = []
        
        try:
            response = self.get_url(url)
        except:
            showErrorMessage("Sorry. Show is not available")
            return
            
        if self.prev == 'show':
            jts = make_dict_from_tree(xml.etree.ElementTree.fromstring(response))['root']
            results = jts['results']['list-item']
        else:
            
            try:
                brdata = re.compile("initialData.branding = '{(.*?)}';").findall(response)[0].decode('unicode-escape')
                brs = json.loads('{'+brdata+'}')
                try: self.fanart = brs['banner'][1]['picture']
                except: self.fanart = brs['banner'][0]['picture']
                self.log(self.fanart)
            except: pass
            
            
            div = common.parseDOM(response, "div", attrs={"id": "page-object"}, ret="data-value")
            if div:
                judata = html_unescape(div[0].decode('unicode-escape')).replace("\n", " ")
                judata = ' '.join(judata.split())
            else:
                try: jtdata = re.compile("initialData.resultsOfActiveTabResources\[(.*?)\] = '{(.*?)}';").findall(response)[0][1].decode('unicode-escape').replace("\n", " ")
                except:
                    try: jtdata = re.compile("initialData.personVideoTab = JSON.parse\('{(.*?)}'\);").findall(response)[0].decode('unicode-escape').replace("\n", " ")
                    except: jtdata = html_unescape(re.compile('data-value="{(.*?)}">').findall(response)[0].decode('unicode-escape')).replace("\n", " ")
    
                judata = '{'+jtdata+'}'

            jts = json.loads(judata)
            results = jts['results']
    
        for res in results:
            self.log(str(res).decode('unicode-escape'))
            name = ''
            url = ''
            pic = ''
            plot = ''
            try:
                name = res['object']['name']
                pic = res['object']['picture']
                url = res['object']['absolute_url']
                plot = res['object']['description']
            except:
                try:
                    name = res['title']
                    pic = res['picture_url']
                    url = res['video_url']
                    plot = res['description']
                except: pass

            if pic == '' or pic == None:
                try: pic = res['thumbnail_url']
                except: pass
            if plot == '' or plot == None:
                try: plot = res['short_description']
                except: pass
            
            self.log("-m_show-name: %s"%name)
            self.log("-m_show-pic: %s"%pic)
            self.log("-m_show-url: %s"%url)
            
            if url and name:
                params = '?mode=play&name=%s&icon=%s&prev=show&url=%s'%(name, QT(pic), QT(url) )
                ct_show.append((params, pic, False, {'title': name, 'plot':plot}))
        
        try: next = str(jts['has_next']).capitalize()
        except: next = ''
            
        if next == 'True':
            params = '?mode=%s&prev=show&url=%s'%('show', QT(jts['next']))
            ct_show.append((params, self.inext, True, {'title': '[COLOR=FFFFD700]' + self.language(2001) + '[/COLOR]'}))


        else: self.log("--has_next:>%s<"%next)
            

        self.listItems(ct_show, True)

    def selectQuality(self, url, data):
        if (self.quality == 'auto') or (not ('#EXTM3U' in data)):
            return url
        else:
          bands = re.compile("BANDWIDTH=.*?, CODECS").findall(data)            
          urls = re.compile("http:\/\/.*?\n").findall(data)
          qlist = [] 
          index = -1
          for i, band in enumerate(bands):
             for qitem in QUALITY_TYPES:
                 band_ = band.split('BANDWIDTH=')[-1].split(', CODECS')[0] 
                 if (int(band_) >= qitem[1]) and (int(band_) <= qitem[2]):
                     qlist.append(qitem[0].upper())
          if (len(qlist) > 1):
              if (self.quality == 'select'): 
                  dialog = xbmcgui.Dialog()
                  index = dialog.select(self.language(3000), qlist)
                  if int(index) < 0:
                      index = -2
              else:
                 for j, qitem in enumerate(qlist):
                     if (qitem[0].upper() == self.quality.upper()):
                         index = j
          else:
              index = -1
          if index == -1:
              return url
          elif index == -2:
              return ""
          else:
              return urls[index].replace("\n", "")

    def play(self, url, name, lock):
        self.log("-play:")
        
        if (lock == "1"):
           showErrorMessage("Content blocked by site")
           return

        uri = None
        uri = self.get_rutube(url)
           
        if uri != None and uri != False:
            if not uri.startswith('http'): uri = 'http:' + uri
            uri = UQT(uri)
            self.dbg_log('- uri: '+  uri + '\n')

            data = self.get_url(uri)
            uri = self.selectQuality(uri, data)
            if (uri == ""):
                return
            
            if 1:
                item = xbmcgui.ListItem(name, path = uri, iconImage=self.icon, thumbnailImage=self.icon)
                xbmcplugin.setResolvedUrl(self.handle, True, item)
            else:
                item = xbmcgui.ListItem(name, iconImage=self.icon, thumbnailImage=self.icon)
                sPlayer = xbmc.Player()
                item.setInfo( type='Video', infoLabels={'title':name.decode('cp1251')})
                item.setProperty('IsPlayable', 'true')
                sPlayer.play(uri, item)
        else:
            showErrorMessage("Sorry. Your region is not supported")

    def fixurl(self, url):
        # turn string into unicode
        if not isinstance(url,unicode):
            url = url.decode('utf8')
    
        # parse it
        parsed = urlparse.urlsplit(url)
    
        # divide the netloc further
        userpass,at,hostport = parsed.netloc.rpartition('@')
        user,colon1,pass_ = userpass.partition(':')
        host,colon2,port = hostport.partition(':')
    
        # encode each component
        scheme = parsed.scheme.encode('utf8')
        user = urllib.quote(user.encode('utf8'))
        
        colon1 = colon1.encode('utf8')
        pass_ = urllib.quote(pass_.encode('utf8'))
        at = at.encode('utf8')
        host = host.encode('idna')
        colon2 = colon2.encode('utf8')
        port = port.encode('utf8')
        path = '/'.join(  # could be encoded slashes!
            urllib.quote(urllib.unquote(pce).encode('utf8'),'')
            for pce in parsed.path.split('/')
        )
        query = urllib.quote(urllib.unquote(parsed.query).encode('utf8'),'=&?/')
        fragment = urllib.quote(urllib.unquote(parsed.fragment).encode('utf8'))
    
        # put it back together
        netloc = ''.join((user,colon1,pass_,at,host,colon2,port))
        return urlparse.urlunsplit((scheme,netloc,path,query,fragment))
    
    def get_url(self, url, data = None, cookie = None, save_cookie = False, referrer = None):
        self.dbg_log('-get_url:' + '\n')
        self.dbg_log('- url:'+  url + '\n')
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36')
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3')
        req.add_header('Accept-Language', 'ru-BY,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6')
        req.add_header('Accept-Encoding', 'gzip, deflate, br')
        req.add_header('Host', 'rutube.ru')        
        if cookie: req.add_header('Cookie', cookie)
        if referrer: req.add_header('Referer', referrer)
        if data: 
            response = urllib2.urlopen(req, data,timeout=30)
        else:
            response = urllib2.urlopen(req,timeout=30)
        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
            link = f.read()
        else:    
            link=response.read()
        if save_cookie:
            setcookie = response.info().get('Set-Cookie', None)
            if setcookie:
                setcookie = re.search('([^=]+=[^=;]+)', setcookie).group(1)
                link = link + '<cookie>' + setcookie + '</cookie>'
        
        response.close()
        return link

    def get_rutube(self, url):
        self.dbg_log('-get_rutube:' + '\n')
        self.dbg_log('- url-in:'+  url + '\n')
        c = 0
        if 'rutube.ru' in url:
            try: videoId = re.findall('rutube.ru/play/embed/(.*?)"', url)[0]
            except:
                try: videoId = re.findall('rutube.ru/video/(.*?)/', url)[0]
                except: return None
            url = 'http://rutube.ru/api/play/options/'+videoId+'?format=json'
            self.dbg_log('- url-req:'+  url + '\n')
            request = urllib2.Request(url)
            request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36')
            try:
                response = urllib2.urlopen(request)
                resp = response.read()
            except:
                    c = 1
                    resp = 'Unsupported region'
                    showErrorMessage(resp)
               
            if not c:
                jsonDict = json.loads(resp)
                link = urllib.quote_plus(jsonDict['video_balancer']['m3u8'])
            else:
                link = None
                self.dbg_log('- xvpngate err:'+  resp + '\n')
                
            return link
        else: 
            return None

    def dbg_log(self, line):
        if self.debug: xbmc.log(line)

    def log(self, message):
        if self.debug:
            print "### %s: %s" % (self.id, message)

    def strip(self, string):
        return common.stripTags(string)

#Helpers
def QT(url): return urllib.quote_plus(url)
def UQT(url): return urllib.unquote_plus(url)

def html_escape(text):
    text = text.replace("&", "&amp;")
    text = text.replace(">", "&gt;")
    text = text.replace("<", "&lt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text

def html_unescape(text):
    return text.replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<").replace("&quot;", '"').replace("&apos;", "'")
 
def make_dict_from_tree(element_tree):

    def internal_iter(tree, accum):

        if tree is None:
            return accum
 
        if tree.getchildren():
            accum[tree.tag] = {}
            for each in tree.getchildren():
                result = internal_iter(each, {})
                if each.tag in accum[tree.tag]:
                    if not isinstance(accum[tree.tag][each.tag], list):
                        accum[tree.tag][each.tag] = [
                            accum[tree.tag][each.tag]
                        ]
                    accum[tree.tag][each.tag].append(result[each.tag])
                else:
                    accum[tree.tag].update(result)
        else:
            accum[tree.tag] = tree.text
 
        return accum
 
    return internal_iter(element_tree, {})

def error(message):
    xbmc.log("[%s ERROR]: %s" % (self.id, message))

def showErrorMessage(msg):
    xbmc.log(msg.encode('utf-8'))
    xbmc.executebuiltin("XBMC.Notification(%s, %s, %s)" % ("ERROR:", msg.encode('utf-8'), str(5 * 1000)))

def encode(string):
    return string.decode('cp1251').encode('utf-8')

def encode2(param):
    try:
        return unicode(param).encode('utf-8')
    except:
        return param

ruTube = RuTube()
ruTube.main()  
