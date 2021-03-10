#!/usr/bin/python
# -*- coding: utf-8 -*-
# Writer (c) 2018-2021, dandy
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
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

socket.setdefaulttimeout(120)

class AmDm():

    def __init__(self):
        self.id = 'plugin.audio.dandy.amdm.ru'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString

        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.url = 'https://amdm.ru'

        self.inext = os.path.join(self.path, 'resources/icons/next.png')

    def main(self):
        self.log("Addon: %s"  % self.id)
        self.log("Handle: %d" % self.handle)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)

        mode = params['mode'] if 'mode' in params else None
        url = urllib.parse.unquote_plus(params['url']) if 'url' in params else None
        page = int(params['page']) if 'page' in params else None
        item = int(params['item']) if 'item' in params else None
        keyword = urllib.parse.unquote_plus(params['keyword']) if 'keyword' in params else None        
        tone = int(params['tone']) if 'tone' in params else 0

        if page == 0:
            xbmc.executebuiltin('Container.Update(%s, replace)' % sys.argv[0])

        elif mode == 'show':
            self.show(url, tone)
        elif mode == 'items':
            self.getItems(url, page, item, keyword)
        elif mode == 'items2':
            self.getItems2(url)
        elif mode == 'subitems2':
            self.getSubItems2(url)
        elif mode == 'alphabet':
            self.alphabet()
        elif mode == 'search':
            self.search()
        elif mode == 'text':
            self.text(url, tone)
        elif mode == 'video':
            self.video(url)
        elif mode == 'akkords':
            self.akkords(url, tone)
        elif mode == 'tone':
            self.tone(url, tone)
        elif mode == 'empty':
            self.empty()
        elif mode is None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + "?mode=search" 
        item = xbmcgui.ListItem("[COLOR=lightgreen]%s[/COLOR]" % self.language(1000))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
    
        self.getMainItems()
    
        uri = sys.argv[0] + "?mode=alphabet" 
        item = xbmcgui.ListItem("[COLOR=orange]%s[/COLOR]" % self.language(1001))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getMainItems(self):
        response = common.fetchPage({"link": self.url})
        if response["status"] == 200:
            content = common.parseDOM(response["content"].decode("utf-8"), "ul", attrs={"class": "sub-menu g-padding sub-menu--active"})[0]
            items = common.parseDOM(content, "li")
            labels = common.parseDOM(items, "a")
            links = common.parseDOM(items, "a", ret="href")
            for i, item in enumerate(labels):
                if (i > 3):
                    break
                uri = sys.argv[0] + "?mode=items&item=%s&url=%s" % (str(i), "https:" + links[i])
                item_ = xbmcgui.ListItem(self.strip(item))
                item_.setArt({ 'thumb': self.icon, 'icon' : self.icon })                
                xbmcplugin.addDirectoryItem(self.handle, uri, item_, True)

    def alphabet(self):
        response = common.fetchPage({"link": self.url})
        if response["status"] == 200:
            content = common.parseDOM(response["content"].decode("utf-8"), "div", attrs={"class": "alphabet g-margin"})[0]
            items = common.parseDOM(content, "li")
            labels = common.parseDOM(items, "a")
            links = common.parseDOM(items, "a", ret="href")

            for i, item in enumerate(labels):
                uri = sys.argv[0] + "?mode=subitems2&url=%s" % (self.url + links[i])
                item_ = xbmcgui.ListItem(self.strip(item))
                item_.setArt({ 'thumb': self.icon, 'icon' : self.icon })                
                xbmcplugin.addDirectoryItem(self.handle, uri, item_, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getSubItems1(self, url):
        response = common.fetchPage({"link": url})
        if response["status"] == 200:
            content = common.parseDOM(response["content"].decode("utf-8"), "ul", attrs={"class": "h1__tabs"})[0]
            items = common.parseDOM(content, "li")
            for i, item in enumerate(items):
                label = common.parseDOM(item, "a")[0] if common.parseDOM(item, "a") else common.parseDOM(item, "span")[0]
                link = self.url + common.parseDOM(item, "a", ret="href")[0] if common.parseDOM(item, "a") else self.url + "/akkordi/popular/"
                uri = sys.argv[0] + "?mode=items&url=%s" % (link)
                item_ = xbmcgui.ListItem(self.strip(label))
                item_.setArt({ 'thumb': self.icon, 'icon' : self.icon })
                xbmcplugin.addDirectoryItem(self.handle, uri, item_, True)
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getSubItems2(self, url):
        response = common.fetchPage({"link": url})
        if response["status"] == 200:
            content = common.parseDOM(response["content"].decode("utf-8"), "table", attrs={"class": "items"})
            items = common.parseDOM(content, "tr")
            photo_tds = common.parseDOM(items, "td", attrs={"class": "photo"})            
            photos = common.parseDOM(photo_tds, "img", ret="src")
            tds = common.parseDOM(items, "td", attrs={"class": "artist_name"}) 
            labels = common.parseDOM(tds, "a")
            links = common.parseDOM(tds, "a", ret="href")

            for i, item in enumerate(labels):
                uri = sys.argv[0] + '?mode=items2&url=%s' % ("https:" + links[i])
                try:
                    photo = ("https:" + photos[i]).replace("33x33", "250")
                except:
                    photo = self.icon
                sub = tds[i]
                numbers = common.parseDOM(items[i], "td", attrs={"class": "number"})
                item_ = xbmcgui.ListItem(self.strip("[COLOR=lightgreen]%s[/COLOR]%s [COLOR=lightblue][%s][/COLOR]" % (labels[i], " - [I]" + sub.split("<br>")[-1] + "[/I]" if "<br>" in sub else "", numbers[0])))
                item.setArt({ 'thumb': photo, 'icon' : photo })
                xbmcplugin.addDirectoryItem(self.handle, uri, item_, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getSubItems3(self, url, page):
        if (not page):
            page = 1
        response =  common.fetchPage({"link": url}) if (not page) else common.fetchPage({"link": url + "page" + str(page) + "/"})

        if response["status"] == 200:
            content = common.parseDOM(response["content"].decode("utf-8"), "table", attrs={"class": "items"})
            items = common.parseDOM(content, "tr")
            photo_tds = common.parseDOM(items, "td", attrs={"class": "photo"})            
            photos = common.parseDOM(photo_tds, "img", ret="src")
            tds = common.parseDOM(items, "td", attrs={"class": "artist_name"}) 
            labels = common.parseDOM(tds, "a")
            links = common.parseDOM(tds, "a", ret="href")

            for i, item in enumerate(labels):
                uri = sys.argv[0] + '?mode=items2&url=%s' % ("https:" + links[i])
                try:
                    photo = ("https:" + photos[i]).replace("33x33", "250")
                except:
                    photo = self.icon
                sub = tds[i]
                numbers = common.parseDOM(items[i], "td", attrs={"class": "number"})
                item_ = xbmcgui.ListItem(self.strip("[COLOR=lightgreen]%s[/COLOR]%s [COLOR=blue][%s][/COLOR]" % (labels[i], " - [I]" + sub.split("<br>")[-1] + "[/I]" if "<br>" in sub else "", numbers[0])))
                item_.setArt({ 'thumb': photo, 'icon' : photo })                
                xbmcplugin.addDirectoryItem(self.handle, uri, item_, True)

            nav = common.parseDOM(response["content"].decode("utf-8"), "ul", attrs={"class": "nav-pages"}) 
            if page and nav:
                uri = sys.argv[0] + "?mode=items&item=3&url=%s&page=%s"%(url, str(page + 1))
                item = xbmcgui.ListItem("[COLOR=orange]%s[/COLOR]" % (self.language(2000)%(str(page + 1))))
                item.setArt({ 'thumb': self.inext })
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getItems(self, url, page, item=0, keyword=None):
        if item == 1:
            self.getSubItems1(url)
            return
        if item == 2:
            self.getSubItems2(url)
            return
        if item == 3:
            self.getSubItems3(url, page)
            return
        if (not page):
            page = 1
        params = {}
        if keyword:
            params = { "q": keyword }  
        if keyword:
	        response =  common.fetchPage({"link": url + "page" + str(page) + "/?" + urllib.parse.urlencode(params)})
        else:
                response =  common.fetchPage({"link": url + "page" + str(page) + "/" })
        if response["status"] == 200:
            content = common.parseDOM(response["content"].decode("utf-8"), "table", attrs={"class": "items"})
            items = common.parseDOM(content, "tr")
            photo_tds = common.parseDOM(items, "td", attrs={"class": "photo"})            
            photos = common.parseDOM(photo_tds, "img", ret="src")
            tds = common.parseDOM(items, "td", attrs={"class": "artist_name"}) 
            labels = common.parseDOM(tds, "a")
            links = common.parseDOM(tds, "a", ret="href")
            label = ""            
            for i, item in enumerate(labels):
                if (i % 2) == 1:
                    uri = sys.argv[0] + '?mode=show&url=%s' % ("https:" + links[i])
                    try:
                        photo = (self.url + photos[(i-1)/2]).replace("33x33", "250")
                    except:
                        photo = self.icon
                    item_ = xbmcgui.ListItem(self.strip("[COLOR=lightgreen]%s[/COLOR]" % label + " - " + labels[i]))
                    item_.setArt({ 'thumb': photo, 'icon' : photo })
                    xbmcplugin.addDirectoryItem(self.handle, uri, item_, True)
                else:
                    label = labels[i]
                    
            nav = common.parseDOM(response["content"].decode("utf-8"), "ul", attrs={"class": "nav-pages"}) 
            if page and nav:
                uri = sys.argv[0] + "?mode=items&url=%s&page=%s"%(url, str(page + 1))
                if keyword:
                    uri = uri + "&keyword=" + urllib.parse.quote_plus(keyword)
                item = xbmcgui.ListItem("[COLOR=orange]%s[/COLOR]" % (self.language(2000)%(str(page + 1))))
                item.setArt({ 'thumb': self.inext })
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
                    
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def getItems2(self, url):
        response =  common.fetchPage({"link": url})
        if response["status"] == 200:
            photo_div = common.parseDOM(response["content"].decode("utf-8"), "div", attrs={"class": "artist-profile__photo debug1"})[0]
            photo = "https:" + common.parseDOM(photo_div, "img", ret="src")[0]
            content = common.parseDOM(response["content"].decode("utf-8"), "table", attrs={"id": "tablesort"})
            items = common.parseDOM(content, "tr")
            labels = common.parseDOM(items, "a")
            links = common.parseDOM(items, "a", ret="href")
 
            for i, item in enumerate(items):
                uri = sys.argv[0] + '?mode=show&url=%s' % ("https:" + links[i])
                item_ = xbmcgui.ListItem(self.strip("%s" % labels[i]))
                item_.setArt({ 'thumb': photo, 'icon' : photo })
                xbmcplugin.addDirectoryItem(self.handle, uri, item_, True)
                    
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def showText(self, heading, text):
        id = 10147
        xbmc.executebuiltin('ActivateWindow(%d)' % id)
        xbmc.sleep(500)
        win = xbmcgui.Window(id)
        retry = 50
        while (retry > 0):
            try:
                xbmc.sleep(10)
                retry -= 1
                win.getControl(1).setLabel(heading)
                win.getControl(5).setText(text)
                return
            except:
                pass

    def show(self, url, tone = 0):
        uri = sys.argv[0] + "?mode=text&tone=%s&url=%s"  % (str(tone), url)
        item = xbmcgui.ListItem("%s" % "[COLOR=lightgreen]" + self.language(3000) + "[/COLOR]")
        item.setArt({ 'thumb': self.icon })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        uri = sys.argv[0] + "?mode=video&url=%s"  % (url)
        item = xbmcgui.ListItem("%s" % self.language(3001))
        item.setArt({ 'thumb': self.icon })
        item.setInfo(type='Video', infoLabels={})
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
        uri = sys.argv[0] + "?mode=akkords&url=%s&tone=%s"  % (url, str(tone))
        item = xbmcgui.ListItem("%s" % self.language(3002))
        item.setArt({ 'thumb': self.icon })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        uri = sys.argv[0] + "?mode=tone&url=%s&tone=%s"  % (url, str(tone))
        item = xbmcgui.ListItem("%s - [COLOR=lightblue]%s[/COLOR]" % (self.language(3003), tone))
        item.setArt({ 'thumb': self.icon })        
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def text(self, url, tone=0):
        response = common.fetchPage({"link": url})
        if response["status"] == 200:
            content = common.parseDOM(response["content"].decode("utf-8"), "div", attrs={"class": "b-podbor "})[0]
            label = common.parseDOM(content, "span", attrs={"itemprop": "byArtist"})[0]
            label += " - " + common.parseDOM(content, "span", attrs={"itemprop": "name"})[0]
            comment = common.parseDOM(response["content"].decode("utf-8"), "pre", attrs={"class": "b-podbor__comment"})
            if tone != 0:
                data = self.getToneData(url, tone)
                jdata = json.loads(data)
                text = jdata["song_text"]
            else:
                text = common.parseDOM(content, "pre", attrs={"itemprop": "chordsBlock"})[0]
            text = text.replace("<b>", "[COLOR orange]")
            text = text.replace("</b>", "[/COLOR]")
            if comment:
                text = "[I]" + comment[0] + "[/I]\n\n" + text
            self.showText(label, text)

    def video(self, url):
        response = common.fetchPage({"link": url})
        if response["status"] == 200:
                try:
                    content = common.parseDOM(response["content"].decode("utf-8"), "div", attrs={"class": "b-video"})[0]
                    data = common.parseDOM(content, "iframe", ret="src")[0]
                    videoId = data.split("/")[-1]
                    link = "plugin://plugin.video.youtube/play/?video_id=" + videoId
                    item = xbmcgui.ListItem(path = link)
                    xbmcplugin.setResolvedUrl(self.handle, True, item)
                except:
                    self.showWarningMessage(self.language(4000))

    def getToneData(self, url, tone):
        data = None
        response = common.fetchPage({"link": url})
        if response["status"] == 200:
            song_id = common.parseDOM(response["content"].decode("utf-8"), "input", attrs={"name": "song_id"}, ret="value")[0]
            link = self.url + "/json/song/transpon/"
            values = { "song_id": song_id,  "tone": tone }
            response = common.fetchPage({"link": link, "post_data": values})
            if response["status"] == 200:
                data = response["content"].decode("utf-8")
        return data
    
    def empty(self):
        return False

    def akkords(self, url, tone=0):
        data = self.getToneData(url, tone)
        jdata = json.loads(data)
        chords = jdata["song_chords"]
        text = jdata["song_text"]
        for chord in chords:
            try:
                chord_ = chords[chord]
            except:
                chord_ = chord    
            image = self.url + "/images/chords/" + chord_.replace('+', 'p').replace('-', 'z').replace('#', 'w').replace('/', 's') + "_0.gif"
            uri = sys.argv[0] + "?mode=empty"
            item = xbmcgui.ListItem(chord_)
            item.setArt({ 'thumb': image })
            xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)
        xbmc.executebuiltin("Container.SetViewMode(0)")
        for i in range(1, 2):
            xbmc.executebuiltin("Container.NextViewMode")
    
    def tone(self, url, tone=0):
        for tone_ in range(13):
            uri = sys.argv[0] + "?mode=show&url=%s&tone=%s"  % (url, str(tone_ - 6))
            item = xbmcgui.ListItem("%s" %  str(tone_ - 6))
            item.setArt({ 'thumb': self.icon })
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def get_user_input(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(2000))
        kbd.doModal()
        keyword = None
        if kbd.isConfirmed():
                keyword = kbd.getText()
        return keyword

    def search(self):
        keyword = self.get_user_input()
        if (not keyword) or (keyword == ""):
            return
            
        self.getItems(self.url + "/search/", 1, 0, keyword)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    # *** Add-on helpers
    def log(self, message):
        print("### %s: %s" % (self.id, message))

    def error(self, message):
        print("%s ERROR: %s" % (self.id, message))

    def showErrorMessage(self, msg):
        print(msg)
        xbmc.executebuiltin("XBMC.Notification(%s, %s, %s)" % ("ERROR", msg, str(5 * 1000)))

    def showWarningMessage(self, msg):
        print(msg)
        xbmc.executebuiltin("XBMC.Notification(%s, %s, %s)" % ("WARNING", msg, str(5 * 1000)))

    def strip(self, string):
        return common.stripTags(string)

    def encode(self, string):
        return string.encode('utf-8')

    def decode(self, string):
        return string.decode('utf-8')

    def strip(self, string):
        return common.stripTags(string)

AmDm = AmDm()
AmDm.main()  
