# tests/test_index.py
import unittest

import support
from support import (
    BUBBLE_HTML, FakeResponse, index_page, index_page_plain, make_plugin, xbmcplugin,
)


def index_plugin(settings=None):
    return make_plugin({('GET', '/'): FakeResponse(text=index_page())}, settings)


class IndexNormalTest(unittest.TestCase):
    def test_movies_playable_serials_folders(self):
        plugin = index_plugin()
        plugin.index(None, None, None)
        self.assertEqual(len(xbmcplugin.ADDED), 2)
        _, movie_url, movie_item, movie_folder = xbmcplugin.ADDED[0]
        _, _, serial_item, serial_folder = xbmcplugin.ADDED[1]
        self.assertIn('Тестовый фильм', movie_item.label)
        self.assertFalse(movie_folder)
        self.assertEqual(movie_item._properties.get('IsPlayable'), 'true')
        self.assertNotIn('atl', movie_url)
        self.assertTrue(serial_folder)

    def test_no_next_page_for_short_list(self):
        plugin = index_plugin()
        plugin.index(None, None, None)
        urls = [url for _, url, _, _ in xbmcplugin.ADDED]
        self.assertFalse([u for u in urls if 'page' in u])


class IndexAtlTest(unittest.TestCase):
    def test_movies_untouched_by_atl(self):
        plugin = index_plugin({'use_atl_names': 'true'})
        plugin.index(None, None, None)
        _, url, item, is_folder = xbmcplugin.ADDED[0]
        self.assertIn('Тестовый фильм', item.label)
        self.assertNotIn('atl', url)
        self.assertNotIn('strm', url)
        self.assertFalse(is_folder)
        self.assertEqual(item._info.get('year'), '2025')

    def test_movie_folder_with_select_quality(self):
        plugin = index_plugin({'use_atl_names': 'true', 'quality': 'select'})
        plugin.index(None, None, None)
        _, url, item, is_folder = xbmcplugin.ADDED[0]
        self.assertTrue(is_folder)
        self.assertNotIn('IsPlayable', item._properties)

    def test_normal_label_keeps_colored_rating(self):
        routes = {
            ('GET', '/'): FakeResponse(text=index_page()),
            ('POST', '/engine/ajax/quick_content.php'): FakeResponse(text=BUBBLE_HTML),
        }
        plugin = make_plugin(routes, {'use_atl_names': 'true', 'show_description': 'true'})
        plugin.index(None, None, None)
        _, _, item, _ = xbmcplugin.ADDED[0]
        self.assertIn('Тестовый фильм', item.label)
        self.assertIn('[COLOR=green][7.5][/COLOR]', item.label)

    def test_serial_untouched(self):
        plugin = index_plugin({'use_atl_names': 'true'})
        plugin.index(None, None, None)
        _, _, item, is_folder = xbmcplugin.ADDED[1]
        self.assertTrue(is_folder)
        self.assertIn('Тестовый сериал', item.label)


class SearchTest(unittest.TestCase):
    def test_external_search_atl_movies_plain(self):
        routes = {('GET', '/search/'): FakeResponse(text=index_page())}
        plugin = make_plugin(routes, {'use_atl_names': 'true'})
        plugin.search('Тест', 'main')
        _, url, item, is_folder = xbmcplugin.ADDED[0]
        self.assertIn('Тестовый фильм', item.label)
        self.assertNotIn('atl', url)
        self.assertNotIn('strm', url)
        self.assertFalse(is_folder)

    def test_plain_markup_without_comments(self):
        for caller in ('index', 'search'):
            routes = {
                ('GET', '/'): FakeResponse(text=index_page_plain()),
                ('GET', '/search/'): FakeResponse(text=index_page_plain()),
            }
            plugin = make_plugin(routes, {'use_atl_names': 'true'})
            if caller == 'index':
                plugin.index(None, None, None)
            else:
                plugin.search('Тест', 'main')
            _, _, item, _ = xbmcplugin.ADDED[0]
            self.assertIn('Тестовый фильм', item.label)
            xbmcplugin.reset()


class AdditionalInfoTest(unittest.TestCase):
    def test_bubble_parsing(self):
        routes = {('POST', '/engine/ajax/quick_content.php'): FakeResponse(text=BUBBLE_HTML)}
        plugin = make_plugin(routes, {'show_description': 'true'})
        info = plugin.get_item_additional_info('1')
        self.assertIn('Описание фильма', info['description'])
        self.assertIn('IMDb', info['description'])
        self.assertEqual(info['age_limit'], '16+')
        self.assertEqual(info['rating']['site'], '7.5')
        self.assertEqual(info['rating']['imdb'], '7.1')
        self.assertEqual(info['rating']['kp'], '6.9')

    def test_skipped_when_disabled(self):
        plugin = make_plugin()
        info = plugin.get_item_additional_info('1')
        self.assertEqual(info['description'], '')
        self.assertEqual(plugin.make_response.calls, [])


if __name__ == '__main__':
    unittest.main()
