# tests/test_helpers.py
import unittest

import support
from support import helpers


class ColorRatingTest(unittest.TestCase):
    def test_bands(self):
        self.assertIn('red', helpers.color_rating('3.5'))
        self.assertIn('yellow', helpers.color_rating('6.0'))
        self.assertIn('green', helpers.color_rating('8.2'))

    def test_empty(self):
        self.assertEqual(helpers.color_rating(''), '')


class MediaAttributesTest(unittest.TestCase):
    def test_three_parts(self):
        self.assertEqual(helpers.get_media_attributes('2025, Россия, Драмы'), ('2025', ' Россия', ' Драмы'))

    def test_two_parts_country_unknown(self):
        year, country, genre = helpers.get_media_attributes('2025, Драмы')
        self.assertEqual((year, country), ('2025', 'Unknown'))

    def test_degenerate_input_defaults(self):
        self.assertEqual(helpers.get_media_attributes(''), ('', 'Unknown', ''))
        self.assertEqual(helpers.get_media_attributes('oops'), ('', 'Unknown', ''))


class BuiltTitleTest(unittest.TestCase):
    def test_contains_name(self):
        title = helpers.built_title('Имя', '2025', rating={'site': ''}, age_limit='', description='')
        self.assertIn('Имя', title)


class CookiesTest(unittest.TestCase):
    def test_roundtrip(self):
        from requests.cookies import create_cookie, RequestsCookieJar
        jar = RequestsCookieJar()
        jar.set_cookie(create_cookie(name='a', value='b', domain='example.com', path='/'))
        dumped = helpers.dump_cookies(jar)
        loaded = helpers.load_cookies(dumped)
        self.assertEqual(loaded.get('a'), 'b')

    def test_broken_input_gives_empty_jar(self):
        loaded = helpers.load_cookies('not-json{{{')
        self.assertEqual(list(loaded), [])

    def test_legacy_dict_format_migrates(self):
        loaded = helpers.load_cookies('{"a": "b", "c": "d"}')
        self.assertEqual(loaded.get('a'), 'b')
        self.assertEqual(loaded.get('c'), 'd')

    def test_garbage_entries_skipped(self):
        loaded = helpers.load_cookies('[ {"name": "a", "value": "b"}, 42, "x", {"value": "noname"} ]')
        self.assertEqual(loaded.get('a'), 'b')
        self.assertEqual(len(list(loaded)), 1)


class SubtitlesTest(unittest.TestCase):
    def test_split(self):
        subs = helpers.get_subtitles({'subtitle': 'ru]http://cdn/ru.vtt,en]http://cdn/en.vtt'})
        self.assertEqual(subs, ['http://cdn/ru.vtt', 'http://cdn/en.vtt'])

    def test_bool_is_none(self):
        self.assertIsNone(helpers.get_subtitles({'subtitle': False}))

    def test_missing_is_none(self):
        self.assertIsNone(helpers.get_subtitles({}))


class SetItemSubtitlesTest(unittest.TestCase):
    def test_list_and_single(self):
        from support import xbmcgui
        item = xbmcgui.ListItem('t')
        helpers.set_item_subtitles(item, ['a'])
        self.assertEqual(item._subtitles, ['a'])
        helpers.set_item_subtitles(item, 'b')
        self.assertEqual(item._subtitles, ['b'])

    def test_none_keeps_empty(self):
        from support import xbmcgui
        item = xbmcgui.ListItem('t')
        helpers.set_item_subtitles(item, None)
        self.assertEqual(item._subtitles, [])


if __name__ == '__main__':
    unittest.main()
