# tests/test_cache.py
import os
import tempfile
import unittest

import support
from support import HDRezkaCache


def fresh_dir():
    return tempfile.mkdtemp(prefix='hdrezka_cache_test_')


class TranslationTest(unittest.TestCase):
    def test_miss_is_none(self):
        cache = HDRezkaCache(fresh_dir())
        self.assertIsNone(cache.get_post_translation('1'))

    def test_set_get_overwrite(self):
        cache = HDRezkaCache(fresh_dir())
        cache.set_post_translation('1', '111')
        self.assertEqual(cache.get_post_translation('1'), '111')
        cache.set_post_translation('1', '56')
        self.assertEqual(cache.get_post_translation('1'), '56')

    def test_posts_isolated(self):
        cache = HDRezkaCache(fresh_dir())
        cache.set_post_translation('1', '111')
        self.assertIsNone(cache.get_post_translation('2'))

    def test_persists_across_instances(self):
        path = fresh_dir()
        cache = HDRezkaCache(path)
        cache.set_post_translation('9', '42')
        del cache
        cache2 = HDRezkaCache(path)
        self.assertEqual(cache2.get_post_translation('9'), '42')


class DetailsTest(unittest.TestCase):
    def test_roundtrip(self):
        cache = HDRezkaCache(fresh_dir())
        cache.set_post_details('7', {'a': [1, 2]})
        self.assertEqual(cache.get_post_details('7'), {'a': [1, 2]})

    def test_miss_is_none(self):
        cache = HDRezkaCache(fresh_dir())
        self.assertIsNone(cache.get_post_details('7'))

    def test_db_file_created(self):
        path = fresh_dir()
        HDRezkaCache(path)
        self.assertTrue(os.path.exists(os.path.join(path, 'cache2.db')))


class NamesTest(unittest.TestCase):
    def test_name_roundtrip(self):
        cache = HDRezkaCache(fresh_dir())
        cache.set_post_translation('1', '111', 'HDrezka Studio')
        self.assertEqual(cache.get_post_translation_name('1'), 'HDrezka Studio')
        self.assertEqual(cache.get_post_translation('1'), '111')

    def test_name_missing_is_none(self):
        cache = HDRezkaCache(fresh_dir())
        cache.set_post_translation('1', '111')
        self.assertIsNone(cache.get_post_translation_name('1'))
        self.assertIsNone(cache.get_post_translation_name('nope'))

    def test_migrates_old_schema(self):
        import sqlite3
        path = fresh_dir()
        conn = sqlite3.connect(os.path.join(path, 'cache2.db'))
        conn.execute('CREATE TABLE posts (post_id text, details text)')
        conn.execute('CREATE UNIQUE INDEX posts_idx ON posts(post_id)')
        conn.execute('CREATE TABLE translations (post_id text, translation text)')
        conn.execute('CREATE UNIQUE INDEX translations_idx ON translations(post_id)')
        conn.execute("INSERT INTO translations (post_id, translation) VALUES ('1', '111')")
        conn.commit()
        conn.close()
        cache = HDRezkaCache(path)
        self.assertEqual(cache.get_post_translation('1'), '111')
        cache.set_post_translation('1', '111', 'HDrezka Studio')
        self.assertEqual(cache.get_post_translation_name('1'), 'HDrezka Studio')


if __name__ == '__main__':
    unittest.main()
