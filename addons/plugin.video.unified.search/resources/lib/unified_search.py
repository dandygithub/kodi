#!/usr/bin/python
# Writer (c) 2012, MrStealth
# Rev. 1.1.1
# License: Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)
# -*- coding: utf-8 -*-

import os
import json
import sqlite3

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

from search_db import SearchDB
from result_db import ResultDB


class UnifiedSearch():
    def __init__(self):
        self.id = 'plugin.video.unified.search'
        self.addon = xbmcaddon.Addon(self.id)
        # self.icon = self.addon.getAddonInfo('icon')
        self.path = self.addon.getAddonInfo('path')
        self.language = self.addon.getLocalizedString

        self.debug = self.addon.getSetting("debug") == 'true'

        database_nc = xbmc.translatePath('special://database')
        try    : database = os.path.normpath(database_nc.decode('utf-8'))
        except : database = os.path.normpath(database_nc)

        self.addons_dir = os.path.dirname(self.path)
        db_index = 27
        while db_index > 0:
            db_name = 'Addons%d.db' % db_index
            db_path = os.path.join(database, db_name)
            self.log("db_path - %s" % (db_path))
            db_index -= 1
            if xbmcvfs.exists(db_path):
                self.addon_db = db_path
                break

        self.supported_addons = self.get_supported_addons()

        self.result_db = ResultDB()
        self.search_db = SearchDB()

    def collect(self, results):
        # INFO: Update counter and compare with a number of supported_addons
        search_id = self.search_db.get_latest_search_id()
        counter = self.search_db.update_counter(search_id)

        self.log("Search counter => %d" % (counter))
        # xbmc.sleep(100)

        if results:
            for result in results:
                if 'is_playable' in result:
                    self.result_db.create(search_id, result['title'].lstrip(), result['url'], result['image'], result['plugin'], result['is_playable'])
                else:
                    self.result_db.create(search_id, result['title'].lstrip(), result['url'], result['image'], result['plugin'])

            if len(self.supported_addons) == counter:
                self.log("ALL DONE => %s of %d done" % (counter, len(self.supported_addons)))
                self.notify("Search", "Done")

                # xbmc.executebuiltin('XBMC.ReplaceWindow(10025, %s, return)' % "plugin://%s/?mode=show&search_id=%d" % (self.id, search_id))
                xbmc.executebuiltin('Container.Update(%s)' % "plugin://%s/?mode=show&search_id=%d" % (self.id, search_id))

            else:
                # self.log("Wait and do nothing => %s of %d done" % (counter, len(self.supported_addons)))
                return True

        else:
            if len(self.supported_addons) == counter:
                self.notify("Search", "Done")
                # INFO:  Fix for ERROR: Control 50 in window 10025 has been asked to focus, but it can't.
                xbmc.executebuiltin('Container.Update(%s)' % "plugin://%s/?mode=show&search_id=%d" % (self.id, search_id))
            else:
              self.log("!!! Nothing found !!!")
              return True

    def get_supported_addons(self):
        disabled_addons = self.get_disabled_addons()
        self.log("disabled_addons - %s" % (str(disabled_addons)))
        supported_addons = []

        for addon in os.listdir(self.addons_dir):
            if  os.path.isdir(os.path.join(self.addons_dir, addon)) and 'plugin.video' in addon and addon not in disabled_addons:
                try:
                    if xbmcaddon.Addon(addon).getSetting('unified_search') == 'true':
                        supported_addons.append(addon)
                except Exception, e:
                    self.error("Exception in get_supported_addons")
                    continue

        return supported_addons

    def get_disabled_addons(self):
        try:
            con = sqlite3.connect(self.addon_db)
            cursor = con.cursor()
            cursor.execute('SELECT idVersion FROM version')
            db_version = cursor.fetchone()
            self.log("db_version - %d" % (db_version))
            if db_version >= 27:
                cursor.execute("SELECT addonID FROM installed WHERE enabled = 0")
            else:
                cursor.execute("SELECT addonID FROM disabled")
            return [x[0] for x in cursor.fetchall()]
        except:
            self.log("Error get disabled addons!!!")
            return []

    def notify(self, header, msg):
        xbmc.executebuiltin("XBMC.Notification(%s,%s,%s)" % ('UnifiedSearch', self.language(2002).encode('utf-8'), '1000'))

    def log(self, message):
        if self.debug:
            xbmc.log("*** %s: %s" % ("UnifiedSearch", message), 3)

    def error(self, message):
        xbmc.log("%s ERROR: %s" % ('UnifiedSearch', message), 3)
