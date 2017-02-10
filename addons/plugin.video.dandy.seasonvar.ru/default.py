#!/usr/bin/python
# Writer (c) 2014-2017, dandy, MrStealth
# Rev. 1.1.0
# -*- coding: utf-8 -*-

import os
import urllib
import sys
import socket
import json

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import XbmcHelpers
common = XbmcHelpers


import Translit as translit
translit = translit.Translit()

socket.setdefaulttimeout(120)

Addon = xbmcaddon.Addon(id='plugin.video.dandy.seasonvar.ru')

import xppod
Decoder = xppod.XPpod(Addon)

# UnifiedSearch module
try:
    sys.path.append(os.path.dirname(__file__)+ '/../plugin.video.unified.search')
    from unified_search import UnifiedSearch
except:
    xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("Warning", 'Please install UnifiedSearch add-on!', str(10 * 1000)))


class Seasonvar():
    def __init__(self):
        self.id = 'plugin.video.dandy.seasonvar.ru'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString

        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.url = 'http://seasonvar.ru'

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.debug = False

    def main(self):
        self.log("Addon: %s"  % self.id)
        self.log("Handle: %d" % self.handle)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)

        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        page = params['page'] if 'page' in params else 1

        keyword = params['keyword'] if 'keyword' in params else None
        unified = params['unified'] if 'unified' in params else None

        if mode == 'play':
            self.playItem(url)
        if mode == 'search':
            self.search(keyword, unified)
        if mode == 'show':
            self.getFilmInfo(url, (params['wm'] == "1"))
        elif mode is None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(2000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.getCategoryItems(self.url)

        xbmc.executebuiltin('Container.SetViewMode(52)')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getCategoryItems(self, url):
        print "*** Get category items %s" % url
        page_url = "%s/" % (url)
        response = common.fetchPage({"link": page_url})

        if response["status"] == 200:
            items = common.parseDOM(response["content"], "div", attrs={"class": "news-block"})
            for item in items:
                titlediv = common.parseDOM(item, "div", attrs={"class": "news-right"})
                title = common.parseDOM(titlediv, "b")[0]
                seasondiv = common.parseDOM(titlediv, "div", attrs={"style": "font-size: 10px;color: #fda901;font-weight: normal;"})
                if seasondiv:
                    title = title + ' (' + seasondiv[0].replace('<b>', '').replace('</b>', '') + ') '
                titleadd = common.parseDOM(titlediv, "div", attrs={"class": "news-right-add"})[0]
                title = self.strip(title + ' [COLOR=FF00FFF0][' + titleadd + '][/COLOR]')
                
                urldiv = common.parseDOM(item, "div", attrs={"class": "news-left"})
                image = common.parseDOM(urldiv, "img", ret="src")[0]
                link = common.parseDOM(urldiv, "a", ret="href")[0]

                uri = sys.argv[0] + '?mode=show&url=%s&wm=1' % (self.url + link)

                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title})

                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
            
#            dateitems = common.parseDOM(response["content"], "div", attrs={"class": "film-list-block"})
#            for dateitem in dateitems:
#                date = common.parseDOM(dateitem, "div", attrs={"class": "ff1"})
#                filmitems = common.parseDOM(dateitem, "div", attrs={"class": "film-list-item"})
#                for filmitem in filmitems:
#                    title = self.strip(self.encode(common.parseDOM(filmitem, "a", attrs={"class": "film-list-item-link"})))
#                    title = title + ' (' + common.parseDOM(filmitem, "span", attrs={"class": ""}) + ')'
#                    title = title + ' (' + datecommon.parseDOM(filmitem, "span", attrs={"class": ""}) + ')'                    
            
            xbmc.executebuiltin('Container.SetViewMode(52)')
            xbmcplugin.endOfDirectory(self.handle, True)

    def getFilmInfo(self, url, withoutmulti=False):
        print "*** getFilmInfo for url %s " % url

        response = common.fetchPage({"link": url})
        image = common.parseDOM(response["content"], 'link', attrs={'rel': 'image_src'}, ret='href')[0]        
        multiseason = common.parseDOM(response["content"], 'div', attrs={'class': 'svtabr_wrap show seasonlist'})

        if (not withoutmulti) and multiseason:
            serialitems = common.parseDOM(multiseason, "h2")
            for serialitem in serialitems:
                url = self.url + common.parseDOM(serialitem, "a", ret="href")[0]
                title = common.parseDOM(serialitem, "a")[0]
                title = title.replace('<span>', '[COLOR=FF00FFF0][').replace('</span>', '][/COLOR]').replace('<small>', '[COLOR=FF00FFF0][').replace('</small>', '][/COLOR]')
                title = ' '.join(title.split()).strip()
                uri = sys.argv[0] + '?mode=show&url=%s&wm=1' % url
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title})
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
           
        else:
            divplayer = common.parseDOM(response["content"], 'div', attrs={'id': 'videoplayer719'})
            jshash = common.parseDOM(divplayer, "script", attrs={"type": "text/javascript"})[0]
            uhash = jshash.split('var pl0 = "')[-1].split('";')[0] if 'var pl0 = "' in jshash else None
            pl_url = Decoder.Decode_String(uhash, 'JpvnsR03Tmwu9xgaGLUXztb7H=' + '\n' + 'fNW5elVDyZIiMoQ1B826cd4YkC')
            response = common.fetchPage({"link": self.url + pl_url})
            json_playlist = json.loads(response["content"])
            playlist = json_playlist['playlist']
            for episode in playlist:
                etitle = self.strip(episode['comment'])
                url = episode['file']
                uri = sys.argv[0] + '?mode=play&url=%s' % url
                item = xbmcgui.ListItem(common.stripTags(etitle), iconImage=image, thumbnailImage=image)
                labels = {'title': etitle, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0}
                item.setInfo(type='Video', infoLabels=labels)
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

        if multiseason:
           xbmc.executebuiltin('Container.SetViewMode(52)')
        else:
           xbmc.executebuiltin('Container.SetViewMode(51)')           

        xbmcplugin.endOfDirectory(self.handle, True)

    def playItem(self, url):
        print "*** play url %s" % url
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

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
        return keyword


    def search(self, keyword, unified):
        print "*** search for keyword %s " % keyword

        keyword = translit.rus(keyword) if unified else self.getUserInput()
        unified_search_results = []
        
        if keyword:
            url = self.url +  '/search?q='+unicode(keyword)+'&x=0&y=0'
            response = common.fetchPage({"link": url})
            searchitems = common.parseDOM(response["content"], 'div', attrs={'class': 'searchResult'})
            for searchitem in searchitems:
                urldiv = common.parseDOM(searchitem, "div", attrs={"class": "searchPoster"})
                url = self.url + common.parseDOM(urldiv, "a", ret="href")[0]
                image = common.parseDOM(urldiv, "img", ret="src")[0]
                titlediv = common.parseDOM(searchitem, "div", attrs={"class": "searchContent"})
                title = common.parseDOM(titlediv, "a")[0]
                seasondiv = common.parseDOM(titlediv, "div", attrs={'class': 'searchSeason'})
                if seasondiv:
                    title = title + ' [COLOR=FF00FFF0][' + seasondiv[0] + '][/COLOR]'                  
            
                if unified:
                    self.log("Perform unified search and return results")
                    unified_search_results.append({'title': title, 'url': url, 'image': image, 'plugin': self.id})
                else:
                    uri = sys.argv[0] + '?mode=show&url=%s&wm=0' % url
                    item = xbmcgui.ListItem(title, thumbnailImage=image)
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

            if unified:
                UnifiedSearch().collect(unified_search_results)
            else: 
                xbmc.executebuiltin('Container.SetViewMode(50)')
                xbmcplugin.endOfDirectory(self.handle, True)

        else:
            self.menu()

    # *** Add-on helpers
    def log(self, message):
        if self.debug:
            print "### %s: %s" % (self.id, message)

    def error(self, message):
        print "%s ERROR: %s" % (self.id, message)

    def showErrorMessage(self, msg):
        print msg
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))

    def strip(self, string):
        return common.stripTags(string)

    def encode(self, string):
        return string.decode('cp1251').encode('utf-8')

Seasonvar = Seasonvar()
Seasonvar.main()
