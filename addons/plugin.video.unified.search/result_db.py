#!/usr/bin/python
# Writer (c) 2012, MrStealth
# Rev. 1.1.1
# License: Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)
# -*- coding: utf-8 -*-

import os
import sqlite3 as sqlite
import xbmcaddon

__addon__ = xbmcaddon.Addon(id='plugin.video.unified.search')
addon_path = __addon__.getAddonInfo('path')


class ResultDB:
    def __init__(self):
        self.filename = os.path.join(addon_path, 'resources/databases', 'results.db')
        self.connect()

    def connect(self):

        # Create directory if not exist
        basedir = os.path.dirname(self.filename)
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        # Create DB file if not exist
        if not os.path.isfile(self.filename):
            print "Create new sqlite file %s" % self.filename
            open(self.filename, 'w').close()

        # Try to avoid => OperationalError: database is locked
        self.db = sqlite.connect(self.filename, timeout=1000, check_same_thread = False)
        self.db.text_factory = str
        self.cursor = self.db.cursor()

        self.execute = self.cursor.execute
        self.commit = self.db.commit()

        self.create_if_not_exists()

    def create_if_not_exists(self):
        try:
            self.execute("CREATE TABLE IF NOT EXISTS results (id INT, search_id INT, title TEXT, url TEXT, image TEXT, plugin TEXT, is_playable BOOL NOT NULL)")
            self.db.commit()
        except sqlite.OperationalError:
            print "Database '%s' is locked" % self.filename
            pass

    def result_id(self):
        self.execute("SELECT MAX(id) FROM results")
        tmp = self.cursor.fetchone()[0]
        counter = tmp + 1 if tmp or tmp == 0 else 1
        return counter

    def find_by_search_id(self, search_id):
        self.execute("SELECT * FROM results WHERE search_id = %d ORDER BY title ASC" % search_id)
        return [{'id': x[0], 'search_id': x[1], 'title': x[2], 'url': x[3], 'image': x[4], 'plugin': x[5], 'is_playable': x[6]} for x in self.cursor.fetchall()]

    def create(self, search_id, title, url, image, plugin, is_playable = False):
        id = self.result_id()
        self.execute('INSERT INTO results(id, search_id, title, url, image, plugin, is_playable) VALUES(?,?,?,?,?,?,?)', (id, search_id, title, url, image, plugin, is_playable))
        self.db.commit()

    def all(self):
        self.execute("SELECT * FROM results ORDER BY id ASC")
        return [{'id': x[0], 'search_id': x[1], 'title': x[2], 'url': x[3], 'image': x[4], 'plugin': x[5], 'is_playable': x[6]} for x in self.cursor.fetchall()]

    def drop(self):
        if os.path.isfile(self.filename):
            self.connect()
            self.execute('DROP TABLE IF EXISTS results')
            self.db.commit()

    def close(self):
        self.cursor.close()
        self.db.close()
