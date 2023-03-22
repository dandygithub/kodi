#!/usr/bin/python
# Writer (c) 2012, MrStealth
# Rev. 1.0.2
# -*- coding: utf-8 -*-

import os, sys, urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
import xbmc, xbmcplugin,xbmcgui,xbmcaddon
import json, XbmcHelpers
import Translit as translit

translit = translit.Translit()
common = XbmcHelpers


class iPlayer():
    def __init__(self):
        self.id = 'plugin.audio.iplayer.fm'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString
        self.handle = int(sys.argv[1])
        self.url = 'https://zvyki.com'

        self.icover = os.path.join(self.path, 'resources/icons/cover.png')
        self.inext = os.path.join(self.path, 'resources/icons/next.png')

    def init(self):
        params = common.getParameters(sys.argv[2])
        mode = url  = None

        mode = params['mode'] if 'mode' in params else None
        url = urllib.parse.unquote_plus(params['url']) if 'url' in params else None

        if mode == 'play':
            self.play(url)
        if mode == 'playlist':
            self.getPlaylist(url)
        if mode == 'genres':
            self.listGenres()
        if mode == 'search':
            self.search()
        elif mode is None:
            self.main()

    def main(self):
        uri = sys.argv[0] + '?mode=%s' % ('search')
        item = xbmcgui.ListItem('[COLOR=FF00FF00]%s[/COLOR]' % self.language(1000))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s' % ('genres')
        item = xbmcgui.ListItem('[COLOR=FF00FFF0]%s[/COLOR]' % self.language(4003))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        uri = sys.argv[0] + '?mode=%s&url=%s' % ('playlist', self.url + '/random')
        item = xbmcgui.ListItem('[COLOR=FF00FFF0]%s[/COLOR]' % self.language(4004))
        item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.getPlaylist(self.url + '/top/page/2/')

    def getPlaylist(self, url):
        page = common.fetchPage({"link": url})
        player_block = common.parseDOM(page["content"].decode("utf-8"), "div", attrs={"class": "player_block"})

        playlist_title = common.parseDOM(player_block, "h1", attrs = { "class": "player_block-title" })[0]
        playlist = common.parseDOM(player_block, "ul", attrs={"id": "playlist"})

        tracks = common.parseDOM(playlist, "li", attrs={"class" : "track"})
        titles = common.parseDOM(tracks, "div", attrs={"class": "playlist-title"})
        links  = common.parseDOM(playlist, "li", attrs={"class" : "track"}, ret="data-mp3")
        durations = common.parseDOM(playlist, "li", attrs={"class": "track"}, ret="data-duration")

        navigation = common.parseDOM(player_block, "li", attrs={"class": "listalka1-l"})

        for i, title in enumerate(titles):
            artist = self.beautify(common.parseDOM(title, "a")[0])
            song   = self.beautify(common.parseDOM(title, "a")[1])

            uri = sys.argv[0] + '?mode=%s&url=%s' % ('play', urllib.parse.quote_plus(links[i]))
            item = xbmcgui.ListItem("%s - %s" % (song, artist))
            item.setArt({ 'thumb': self.icover, 'icon' : self.icover })
            item.setProperty('IsPlayable', 'true')
            item.setProperty('mimetype', 'audio/mpeg')

            item.setInfo(
                type='music',
                infoLabels={
                    'title': song,
                    'artist': artist,
                    'album': self.beautify(playlist_title),
                    'genre': 'iplayer.fm',
                    'duration': self.duration(durations[i])
                }
            )

            xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

        if navigation:
            self.navigation('playlist', url)

        xbmcplugin.endOfDirectory(self.handle, True)

    def navigation(self, mode, url):
        if 'page' in url:
            page = int(url[-2:].replace('/', ''))+1
            link = "%s%d/" % (url[:-2], page)
        else:
            link = url + '/page/2/'

        uri = sys.argv[0] + '?mode=%s&url=%s' % (mode, urllib.parse.quote_plus(link))
        item = xbmcgui.ListItem('[COLOR=orange]%s[/COLOR]' % self.language(10000))
        item.setArt({ 'thumb': self.inext, 'icon' : self.inext })
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

    def listGenres(self):
        page = common.fetchPage({"link": self.url})
        styles = common.parseDOM(page["content"].decode("utf-8"), "ul", attrs={"id": "music_styles"})

        genres = common.parseDOM(styles, "a")
        links = common.parseDOM(styles, "a", ret="href")

        for i, genre in enumerate(genres):
            if (links[i] != "/"):
                uri = sys.argv[0] + '?mode=%s&url=%s' % ('playlist', urllib.parse.quote(self.url + links[i]))
                item = xbmcgui.ListItem(genre)
                item.setArt({ 'thumb': self.icon, 'icon' : self.icon })
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.endOfDirectory(self.handle, True)

    def play(self, url):
        print("*** play URL %s" % url)
        item = xbmcgui.ListItem(path=url)
        item.setArt({ 'thumb': self.icover, 'icon' : self.icover })
        item.setProperty('mimetype', 'audio/mpeg')
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def search(self):
        query = common.getUserInput(self.language(1000), "")

        if query:
            if self.addon.getSetting('translit') == 'true':
                print("Module translit enabled")
            try:
                keyword = translit.rus(query)
            except Exception:
                keyword = query

        url = self.url + "/q/" + urllib.parse.quote_plus(keyword.decode("utf-8"))
        self.getPlaylist(url)

    # HELPERS
    def beautify(self, string):
        return common.stripTags(string).replace('&quot;', '').replace('&amp;', '&').capitalize()

    def duration(self, time):
        return int(time)/1000

    def showErrorMessage(self, msg):
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10*1000)))

    def encode(self, string):
        return string.encode('utf-8')


plugin = iPlayer()
plugin.init()
