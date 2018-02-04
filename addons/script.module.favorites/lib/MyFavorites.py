#!/usr/bin/python
# Writer (c) 2012-2017, MrStealth, dandy
# Rev. 2.1.0
# -*- coding: utf-8 -*-
# License: GPLv3

import os
import sys
import urllib

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import sqlite3 as sqlite

# sys.path.append (xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'lib' ) ))

class MyFavoritesDB():
    def __init__(self, plugin):
        self.addon = xbmcaddon.Addon(plugin)
        self.database_file = os.path.join(xbmc.translatePath(self.addon.getAddonInfo('profile')), 'favorites.sqlite')

        print self.database_file
        self.connect()

    def create_if_not_exists(self):
        if not os.path.exists(self.database_file):
            file(self.database_file, 'w').close()

        try:
            self.execute("CREATE TABLE IF NOT EXISTS favorites (title TEXT, url TEXT, image TEXT, playable BOOL NOT NULL)")
            self.db.commit()
        except sqlite.OperationalError:
            print "Database '%s' is locked" % self.filename
            pass

    def connect(self):
        # Create directory if not exist
        basedir = os.path.dirname(self.database_file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        # Create DB file if not exist
        if not os.path.isfile(self.database_file):
            print "Create new sqlite file %s" % self.database_file
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
        self.execute("SELECT * FROM favorites ORDER BY title ASC")
        return [{'title': x[0], 'url': x[1], 'image': x[2], 'playable': x[3]} for x in self.cursor.fetchall()]

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

        self.context_menu = os.path.join(os.path.join(self.path, 'lib' ), 'ContextMenuHandler.py')
        self.database = MyFavoritesDB(self.plugin)
        self.debug = self.addon.getSetting("debug") == 'true'


    # === XBMC Helpers
    def ListItem(self, title=None):
        print self.plugin
        title = title if title else self.language(1000)
        item = xbmcgui.ListItem(title, iconImage=self.icon)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), "plugin://%s/?mode=favorites" % (self.plugin), item, True)

    def addContextMenuItem(self, item, params):
        runner = "XBMC.RunScript(%s,%s)" % (self.context_menu, urllib.urlencode(params))

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
                print "*** Playable item"
                uri = sys.argv[0] + '?mode=play&url=%s' % favorite['url']

                item = xbmcgui.ListItem(favorite['title'], iconImage = favorite['image'])
                self.addContextMenuItem(item, {'title': favorite['title'], 'action': 'remove', 'plugin': self.plugin})
                item.setProperty('IsPlayable', 'true')

                xbmcplugin.addDirectoryItem(int(sys.argv[1]), uri, item, False)
            else:
                print "Show mode"
                uri = sys.argv[0] + '?mode=show&url=%s' % favorite['url']

                item = xbmcgui.ListItem(favorite['title'], iconImage = favorite['image'])
                self.addContextMenuItem(item, {'title': favorite['title'], 'action': 'remove', 'plugin': self.plugin})
                item.setProperty('IsPlayable', 'false')

                xbmcplugin.addDirectoryItem(int(sys.argv[1]), uri, item, True)

        else:
          item = xbmcgui.ListItem(self.language(1005), iconImage = self.icon)
          xbmcplugin.addDirectoryItem(int(sys.argv[1]), '', item, False)


    # === COMMON FUNCTIONS
    def encode(self, string):
        return string.decode('cp1251').encode('utf-8')

    def log(self, message):
        if self.debug:
            print "=== %s: %s" % ("MyFavorites.py", message)

    def error(self, message):
        print "%s ERROR: %s" % (self.id, message)


