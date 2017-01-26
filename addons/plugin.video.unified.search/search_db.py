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


class SearchDB:
    def __init__(self):
        self.filename = os.path.join(addon_path, 'resources/databases', 'searches.db')
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

        # Try to avoid  OperationalError: database is locked
        self.db = sqlite.connect(self.filename, timeout=1000, check_same_thread = False)
        self.db.text_factory = str
        self.cursor = self.db.cursor()
        self.execute = self.cursor.execute
        self.commit = self.db.commit()

        self.create_if_not_exists()

    def create_if_not_exists(self):
        try:
            self.execute("CREATE TABLE IF NOT EXISTS searches (id INT, keyword TEXT, counter INT default 0)")
            self.db.commit()
        except sqlite.OperationalError:
            print "Database '%s' is locked" % self.filename
            pass

    def new(self, keyword):
        search_id = self.search_id()
        self.execute('INSERT INTO searches(id, keyword) VALUES(?,?)', (search_id, keyword))
        self.db.commit()
        return search_id

    def search_id(self):
        self.execute("SELECT MAX(id) FROM searches")
        return self.increase_counter(self.cursor.fetchone()[0])

    def increase_counter(self, counter):
        counter = counter + 1 if counter or counter == 0 else 1
        return counter

    def  get_latest_search_id(self):
        self.execute("SELECT MAX(id) FROM searches")
        return self.cursor.fetchone()[0]

    def update_counter(self, search_id):
        self.execute("UPDATE searches SET counter=counter+1 WHERE id=%d" % (search_id))
        self.execute("SELECT MAX(counter) FROM searches WHERE id=%d" % search_id)
        self.db.commit()

        return self.cursor.fetchone()[0]

    def all(self):
        self.execute("SELECT * FROM searches ORDER BY id DESC")
        return [{'id': x[0], 'keyword': x[1], 'counter': x[2]} for x in self.cursor.fetchall()]

    def drop(self):
        if os.path.isfile(self.filename):
            self.connect()
            self.execute('DELETE FROM searches')
            self.db.commit()

    def close(self):
        self.cursor.close()
        self.db.close()
