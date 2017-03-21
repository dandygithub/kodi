#!/usr/bin/python
# Writer (c) 2012-2017, MrStealth
# Rev. 2.4.0
# License: Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import urllib

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon

import XbmcHelpers
common = XbmcHelpers

import Translit as translit
translit = translit.Translit()

from resources.lib.search_db import SearchDB
from resources.lib.result_db import ResultDB

from resources.lib.unified_search import UnifiedSearch

# TODO:
# 1) Allow to lookup the whitespaced strings <A> <B> => "A+B"

#consts
CHECK_PERIOD = 3000

class UnifiedSearchPlugin():
    def __init__(self):
        self.id = 'plugin.video.unified.search'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')
        self.language = self.addon.getLocalizedString

        self.xpath = sys.argv[0]
        self.handle = int(sys.argv[1])
        self.params = sys.argv[2]

        self.supported_addons = UnifiedSearch().get_supported_addons()
        self.result_db = ResultDB()
        self.search_db = SearchDB()

        self.latest_search_id = self.search_db.get_latest_search_id()
        self.search_id = self.latest_search_id if self.latest_search_id else 0
        self.debug = self.addon.getSetting("debug") == 'true'
        self.timeout = int(self.addon.getSetting("timeout"))

        # Custom icons
        self.search_icon = os.path.join(self.path, 'resources/icons/search.png')
        self.folder_icon = os.path.join(self.path, 'resources/icons/folder.png')
        self.warning_icon = os.path.join(self.path, 'resources/icons/warning.png')

    def main(self):
        self.log("Xpath: %s" % self.xpath)
        self.log("Addon: %s"  % self.id)
        self.log("Handle: %d" % self.handle)
        self.log("Params: %s" % self.params)

        params = common.getParameters(self.params)
        mode = params['mode'] if 'mode' in params else None
        keyword = params['keyword'] if 'keyword' in params else None
           
        search_id = int(params['search_id']) if('search_id' in params) else None
        if search_id == -1:
            search_id = self.search_id

        url = params['url'] if 'url' in params else None
        plugin = params['plugin'] if 'plugin' in params else None
        playable = bool(params['playable']) if 'playable' in params else False

        if mode == 'search':
            self.search(keyword)
        if mode == 'show':
            self.show(search_id)
        if mode == 'previous':
            self.previous_results()
        if mode == 'activate':
            self.activate(plugin, url, playable)
        if mode == 'reset':
            self.reset()
        if mode == 'collect':
            self.collect(self.searchParamsToList(params))
        elif mode is None:
            self.menu()

    # === XBMC VIEWS
    def menu(self):
        self.log("Supported add-ons: %s" % self.supported_addons)

        uri = self.xpath + '?mode=%s' % "search"
        item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(1000), iconImage=self.search_icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        item = xbmcgui.ListItem("%s" % self.language(1001), iconImage=self.folder_icon)
        xbmcplugin.addDirectoryItem(self.handle, "%s?mode=show&search_id=-1" % (self.xpath), item, True)

        item = xbmcgui.ListItem("%s" % self.language(1002), iconImage=self.folder_icon)
        xbmcplugin.addDirectoryItem(self.handle, "%s?mode=previous" % self.xpath, item, True)

        item = xbmcgui.ListItem("[COLOR=FFFF4000]%s[/COLOR]" % self.language(1003), iconImage=self.warning_icon)
        xbmcplugin.addDirectoryItem(self.handle, self.xpath + '?mode=reset', item, False)

        #xbmc.executebuiltin('Container.SetViewMode(50)')
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def search(self, keyword):
        external = False
        if keyword:
            external = True
            keyword = urllib.unquote_plus(keyword)
        else: 
            keyword = self.get_user_input()

        if keyword:
            self.log("Call other add-ons and pass keyword: %s" % keyword)

            # INFO: Generate new search id and save it
            self.search_id = self.search_db.new(keyword)
            keyword = translit.eng(keyword) if self.isCyrillic(keyword) else keyword

            for i, plugin in enumerate(self.supported_addons):
                script = "special://home/addons/%s/default.py" % plugin
                xbmc.executebuiltin("XBMC.RunScript(%s, %d, mode=search&keyword=%s&unified=True)" % (script, self.handle, keyword), True)

            self.notify(self.language(1000).encode('utf-8'), self.language(2000).encode('utf-8'))

            checkEnd = False
            timeout_ = 0
            while (checkEnd == False):
                xbmc.sleep(CHECK_PERIOD) 
                timeout_ += CHECK_PERIOD
                try: 
                    counter = self.search_db.get_counter(self.search_id)
                except: 
                    pass
                if (counter and (len(self.supported_addons) == counter)) or (timeout_ > self.timeout*1000):
                    self.log("ALL DONE => %s of %d done" % (counter, len(self.supported_addons)))
                    checkEnd = True;

            self.notify("Search", "Done")
            self.show(self.search_id, external)
            #xbmc.executebuiltin('Container.Update(%s)' % "plugin://%s/?mode=show&search_id=%d" % (self.id, search_id))

    def searchParamsToList(self, params):
       searchList = []
       searchList.append({'title': params['title'] if 'title' in params else None, 
                          'url': params['url'] if 'url' in params else None, 
                          'image': params['image'] if 'image' in params else None, 
                          'plugin': params['id'] if 'id' in params else None 
                         })
       return searchList

    def collect(self, searchList):
        UnifiedSearch().collect(searchList)

    def show(self, search_id, external = False):
        self.log("Show results on separate page for search_id")
        results = self.result_db.find_by_search_id(search_id) if search_id else []

        if results:
            for i, item in enumerate(results):
                image = item['image'] if item['image']  else self.icon

                if item['is_playable']:
                    uri = '%s?mode=activate&plugin=%s&url=%s&playable=True' % (self.xpath, item['plugin'], item['url'])
                    item = xbmcgui.ListItem("%s (%s)" % (item['title'], item['plugin'].replace('plugin.video.', '')), thumbnailImage=image)
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
                else:
                    uri = '%s?mode=activate&plugin=%s&url=%s' % (self.xpath, item['plugin'], item['url'])
                    item = xbmcgui.ListItem("%s (%s)" % (item['title'], item['plugin'].replace('plugin.video.', '')), thumbnailImage=image)
                    xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
        else:
            if external == False:
                if search_id or search_id == 0:
                    item = xbmcgui.ListItem("[COLOR=FFFF4000]%s[/COLOR]" % self.language(2001))
                    item.setProperty('IsPlayable', 'false')
                    xbmcplugin.addDirectoryItem(self.handle, '', item, False)
                else:
                    item = xbmcgui.ListItem(self.language(2000))
                    item.setProperty('IsPlayable', 'false')
                    xbmcplugin.addDirectoryItem(self.handle, '', item, False)

        #xbmc.executebuiltin('Container.SetViewMode(50)')
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def previous_results(self):
        self.log("Show search result")
        search_results = self.search_db.all()

        if search_results:
            for i, result in enumerate(search_results):
                uri = '%s?mode=show&search_id=%d' % (self.xpath, result['id'])
                item = xbmcgui.ListItem("%02d. %s [%d]" % (result['id'], translit.rus(result['keyword']), result['counter']), thumbnailImage=self.icon)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        else:
            item = xbmcgui.ListItem("[COLOR=FFFF4000]%s[/COLOR]" % self.language(2001))
            item.setProperty('IsPlayable', 'false')
            xbmcplugin.addDirectoryItem(self.handle, '', item, False)

        #xbmc.executebuiltin('Container.SetViewMode(50)')
        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def activate(self, plugin, url, playable):
        self.log("Playable %r %s => %s" % (plugin, url, playable))
        window = "plugin://%s/?mode=show&url=%s" % (plugin, url)

        if playable:
            xbmc.Player().play(window)
            xbmcplugin.endOfDirectory(self.handle, True)
        else:
            xbmc.executebuiltin('Container.Update(%s)' % window)

    def reset(self):
        self.result_db.drop()
        self.search_db.drop()
        xbmc.executebuiltin("Container.refresh()")

    # === HELPERS
    def get_user_input(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(1000))
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            keyword = kbd.getText()

        return keyword

    def log(self, message):
        if self.debug:
            print "=== %s: %s" % ("UnifiedSearch::Plugin", message)

    def error(self, message):
        print "%s ERROR: %s" % (self.id, message)

    def notify(self, header, msg):
        xbmc.executebuiltin("Notification(%s,%s,%s,%s)" % ('UnifiedSearch', msg, '30000', self.icon))

    def isCyrillic(self, keyword):
        if not re.findall(u"[\u0400-\u0500]+", keyword):
            return False
        else:
            return True


UnifiedSearchPlugin().main()