import json
import os
import sqlite3
import time

__all__ = ['HDRezkaCache']


class HDRezkaCache(object):

    def __init__(self, cache_dir):
        # Schema evolves in place via _ensure_schema; a version bump requires
        # migrating data from the old file (bumps orphan it).
        self._version = 2

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        db_path = os.path.join(cache_dir, 'cache{0}.db'.format(self._version))
        db_exist = os.path.exists(db_path)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = self._dict_factory

        if not db_exist:
            self.create_database()
        self._ensure_schema()

    def __del__(self):
        try:
            self.conn.close()
        except AttributeError:
            pass

    @staticmethod
    def _dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def create_database(self):
        c = self.conn.cursor()
        c.execute('CREATE TABLE posts (post_id text, details text)')
        c.execute('CREATE UNIQUE INDEX posts_idx ON posts(post_id)')
        c.execute('CREATE TABLE translations (post_id text, translation text, name text)')
        c.execute('CREATE UNIQUE INDEX translations_idx ON translations(post_id)')
        c.execute('CREATE TABLE bubbles (post_id text, details text, updated integer)')
        c.execute('CREATE UNIQUE INDEX bubbles_idx ON bubbles(post_id)')

        self.conn.commit()

    def _ensure_schema(self):
        try:
            columns = [row['name'] for row in self.conn.execute('PRAGMA table_info(translations)').fetchall()]
        except Exception:
            return
        if 'name' not in columns:
            try:
                self.conn.execute('ALTER TABLE translations ADD COLUMN name TEXT')
                self.conn.commit()
            except Exception:
                pass
        try:
            self.conn.execute('CREATE TABLE IF NOT EXISTS bubbles (post_id TEXT, details TEXT, updated INTEGER)')
            self.conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS bubbles_idx ON bubbles(post_id)')
            self.conn.commit()
        except Exception:
            pass

    def get_post_details(self, post_id):
        sql_params = {'post_id': post_id}

        c = self.conn.cursor()
        c.execute('SELECT details FROM posts WHERE post_id = :post_id LIMIT 1', sql_params)

        result = c.fetchone()
        if result is not None:
            return json.loads(result['details'])

    def set_post_details(self, post_id, details):
        sql_params = {'post_id': post_id, 'details': json.dumps(details)}

        c = self.conn.cursor()
        c.execute('INSERT OR REPLACE INTO posts (post_id, details) VALUES (:post_id, :details)', sql_params)

        self.conn.commit()

    def get_post_translation(self, post_id):
        sql_params = {'post_id': post_id}

        c = self.conn.cursor()
        c.execute('SELECT translation FROM translations WHERE post_id = :post_id LIMIT 1', sql_params)

        result = c.fetchone()
        if result is not None:
            return result['translation']

    def get_post_translation_name(self, post_id):
        sql_params = {'post_id': post_id}

        try:
            c = self.conn.cursor()
            c.execute('SELECT name FROM translations WHERE post_id = :post_id LIMIT 1', sql_params)
        except Exception:
            return None

        result = c.fetchone()
        if result is not None:
            return result['name'] or None
        return None

    def set_post_translation(self, post_id, translation, name=None):
        sql_params = {'post_id': post_id, 'translation': translation, 'name': name}

        c = self.conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO translations (post_id, translation, name) VALUES (:post_id, :translation, :name)', sql_params)
        except Exception:
            self._ensure_schema()
            c.execute('INSERT OR REPLACE INTO translations (post_id, translation, name) VALUES (:post_id, :translation, :name)', sql_params)

        self.conn.commit()

    def get_bubble(self, post_id, ttl):
        sql_params = {'post_id': post_id}

        try:
            c = self.conn.cursor()
            c.execute('SELECT details, updated FROM bubbles WHERE post_id = :post_id LIMIT 1', sql_params)
        except Exception:
            return None

        result = c.fetchone()
        if result is None:
            return None
        try:
            if time.time() - float(result['updated'] or 0) > ttl:
                return None
            return json.loads(result['details'])
        except Exception:
            return None

    def set_bubble(self, post_id, details, ttl):
        now = time.time()
        sql_params = {'post_id': post_id, 'details': json.dumps(details), 'updated': now}

        c = self.conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO bubbles (post_id, details, updated) VALUES (:post_id, :details, :updated)', sql_params)
        except Exception:
            self._ensure_schema()
            c.execute('INSERT OR REPLACE INTO bubbles (post_id, details, updated) VALUES (:post_id, :details, :updated)', sql_params)
        try:
            c.execute('DELETE FROM bubbles WHERE updated < :expiry', {'expiry': now - ttl})
        except Exception:
            pass

        self.conn.commit()
