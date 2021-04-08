#!/usr/bin/python
# Writer (c) 2012-2021, MrStealth, dandy
# -*- coding: utf-8 -*-
# License: GPLv3

import os
import sys
import urllib.request, urllib.parse, urllib.error
import simplejson as json

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import sqlite3 as sqlite

SHOW = "mode=show&url=%s"
PLAY = "mode=play&url=%s"

REQUEST = {'jsonrpc': '2.0',
           'method': '{0}',
           'params': '{1}',
           'id': 1
           }

class MyFavoritesDB():
    def __init__(self, plugin, withCreate):
        if plugin:
            self.addon = xbmcaddon.Addon(plugin)
            self.database_file = os.path.join(xbmc.translatePath(self.addon.getAddonInfo('profile')), 'favorites.sqlite')
            self.existDB = os.path.isfile(self.database_file)
            if ((self.existDB == True) or (withCreate == True)):
                self.connect()

    def create_if_not_exists(self):
        if not os.path.exists(self.database_file):
            file(self.database_file, 'w').close()
        try:
            self.execute("CREATE TABLE IF NOT EXISTS favorites (title TEXT, url TEXT, image TEXT, playable BOOL NOT NULL)")
            self.db.commit()
        except sqlite.OperationalError:
            print("Database '%s' is locked" % self.filename)
            pass

    def connect(self):
        # Create directory if not exist
        basedir = os.path.dirname(self.database_file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        # Create DB file if not exist
        if not os.path.isfile(self.database_file):
            print("Create new sqlite file %s" % self.database_file)
            open(self.database_file, 'w').close()

        self.db = sqlite.connect(self.database_file, timeout=1000, check_same_thread = False)
        self.db.text_factory = str
        self.cursor = self.db.cursor()

        self.execute = self.cursor.execute
        self.commit = self.db.commit()

        self.create_if_not_exists()

    def save(self, title, url, image, playable = False):
        self.execute("SELECT title FROM favorites WHERE title = '%s'" % title)

        if self.cursor.fetchone() is None:
            self.execute('INSERT INTO favorites VALUES(?,?,?,?)', (title, url, image, playable))
            self.db.commit()

    def remove(self, title):
        self.execute("DELETE FROM favorites WHERE title = '%s'" % title)
        self.db.commit()

    def all(self):
        try:
            self.execute("SELECT * FROM favorites ORDER BY title ASC")
            return [{'title': x[0], 'url': x[1], 'image': x[2], 'playable': x[3]} for x in self.cursor.fetchall()]
        except:
            return [] 

    def drop(self):
        if os.path.isfile(self.filename):
            self.connect()
            self.execute('DROP TABLE IF EXISTS results')
            self.db.commit()

    def close(self):
        self.cursor.close()
        self.db.close()


class MyFavorites():
    def __init__(self, plugin):
        self.id = 'script.module.favorites'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')

        self.path = self.addon.getAddonInfo('path')
        self.language = self.addon.getLocalizedString
        self.plugin = plugin

        self.context_menu = os.path.join(os.path.join(self.path, 'lib'), 'ContextMenuHandler.py')
        self.database = MyFavoritesDB(self.plugin, True)
        self.debug = self.addon.getSetting("debug") == 'true'


    def jsonrpc(self, method, params):
        request = REQUEST
        request['method'] = method
        request['params'] = params
        response = xbmc.executeJSONRPC(json.dumps(request))
        j = json.loads(response)
        return j.get('result')

    def getAddons(self):
        result = self.jsonrpc("Addons.GetAddons", {'type': 'xbmc.addon.video', 'content': 'video', 'installed': True, 'enabled': True, 'properties': ['name']})
        return result.get("addons"), result.get("limits")

    # === XBMC Helpers
    def ListItem(self, title=None):
        print(self.plugin)
        title = title if title else self.language(1000)
        item = xbmcgui.ListItem(title)
        item.setArt({ 'icon' : self.icon })        
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), "plugin://%s/?mode=favorites" % (self.plugin), item, True)

    def addContextMenuItem(self, item, params):
        runner = "XBMC.RunScript(%s,%s)" % (self.context_menu, urllib.parse.urlencode(params))

        if params['action'] == 'add':
            item.addContextMenuItems([(self.language(1001), runner)])
        elif params['action'] == 'remove':
            item.addContextMenuItems([(self.language(1002), runner)])
        else:
            self.log("Unknown action '%s' in self.addContextMenuItem()") % params['action']


    def list(self):
        self.log("*** List favorites")
        favorites = self.database.all()

        if favorites:
          for favorite in favorites:
            if favorite['playable']:
                print("*** Playable item")
                uri = sys.argv[0] + '?' + PLAY % favorite['url']

                item = xbmcgui.ListItem(favorite['title'])
                item.setArt({ 'icon' : favorite['image'] })
                self.addContextMenuItem(item, {'title': favorite['title'], 'action': 'remove', 'plugin': self.plugin})
                item.setProperty('IsPlayable', 'true')

                xbmcplugin.addDirectoryItem(int(sys.argv[1]), uri, item, False)
            else:
                print("Show mode")
                uri = sys.argv[0] + '?' + SHOW % favorite['url']

                item = xbmcgui.ListItem(favorite['title'])
                item.setArt({ 'icon' : favorite['image'] })                
                self.addContextMenuItem(item, {'title': favorite['title'], 'action': 'remove', 'plugin': self.plugin})
                item.setProperty('IsPlayable', 'false')

                xbmcplugin.addDirectoryItem(int(sys.argv[1]), uri, item, True)

        else:
          item = xbmcgui.ListItem(self.language(1005))
          item.setArt({ 'icon' : self.icon })
          xbmcplugin.addDirectoryItem(int(sys.argv[1]), '', item, False)


    def listEx(self):
        self.log("*** List all favorites")

        addons, limits = self.getAddons()
        exist = False
        for addon in addons:
          addon_id = addon['addonid']
          addon_name = addon['name']
          addon_object = xbmcaddon.Addon(addon_id)
          self.database = MyFavoritesDB(addon_id, False)
          favorites = self.database.all()
          if favorites:
            for favorite in favorites:
              exist = True
              uri = 'plugin://' + addon_id + '/?' + (PLAY if favorite['playable'] else SHOW) % favorite['url']

              item = xbmcgui.ListItem("[COLOR=orange][" + addon_name + "][/COLOR] " + favorite['title'])
              item.setArt({ 'icon' : favorite['image'] })
              item.setProperty('IsPlayable', "true" if favorite['playable'] else "false")

              xbmcplugin.addDirectoryItem(int(sys.argv[1]), uri, item, not favorite['playable'])
        
        if exist == False:
          item = xbmcgui.ListItem(self.language(1005))
          item.setArt({ 'icon' : self.icon })          
          xbmcplugin.addDirectoryItem(int(sys.argv[1]), '', item, False)

        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

    # === COMMON FUNCTIONS
    def encode(self, string):
        return string.encode('utf-8')

    def log(self, message):
        if self.debug:
            print("=== %s: %s" % ("MyFavorites.py", message))

    def error(self, message):
        print("%s ERROR: %s" % (self.id, message))


