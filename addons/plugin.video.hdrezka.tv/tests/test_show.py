# tests/test_show.py
import unittest

import support
from support import (
    EPISODES_JSON, FakeResponse, GET_STREAM_JSON, MOVIE_AJAX_OK,
    STREAMS_BLOCK, ANUBIS_HTML, TRANSLATORS_DIV, index_page, make_plugin,
    movie_page, router, series_page, xbmcgui, xbmcplugin,
)
from cache import HDRezkaCache


def series_routes(page=None):
    return {
        ('GET', '/series/x.html'): FakeResponse(text=page or series_page()),
        ('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=EPISODES_JSON),
    }


def cached(plugin, post_id, translator_id):
    HDRezkaCache(plugin.profile).set_post_translation(post_id, translator_id)


class SeriesNormalTest(unittest.TestCase):
    def test_translator_line_and_labels(self):
        plugin = make_plugin(series_routes())
        cached(plugin, '92422', '56')
        plugin.show('/series/x.html', False, None)
        first = xbmcplugin.ADDED[0]
        self.assertTrue(first[3])
        self.assertIn('Дубляж', first[2].label)
        labels = [item.label for _, _, item, _ in xbmcplugin.ADDED[1:]]
        self.assertEqual(labels, ['1 серия (Сезон 1)', '2 серия (Сезон 1)', '3 серия (Сезон 2)'])
        self.assertEqual(xbmcgui.Dialog.select_calls, [])

    def test_episodes_playable_with_quality(self):
        plugin = make_plugin(series_routes())
        cached(plugin, '92422', '56')
        plugin.show('/series/x.html', False, None)
        _, url, item, is_folder = xbmcplugin.ADDED[1]
        self.assertFalse(is_folder)
        self.assertEqual(item._properties.get('IsPlayable'), 'true')
        self.assertNotIn('strm', url)

    def test_episodes_are_folders_when_quality_select(self):
        plugin = make_plugin(series_routes(), {'quality': 'select'})
        cached(plugin, '92422', '56')
        plugin.show('/series/x.html', False, None)
        _, _, item, is_folder = xbmcplugin.ADDED[1]
        self.assertTrue(is_folder)
        self.assertNotIn('IsPlayable', item._properties)

    def test_no_dialog_on_cache_miss_when_default(self):
        plugin = make_plugin(series_routes())
        plugin.show('/series/x.html', False, None)
        self.assertEqual(xbmcgui.Dialog.select_calls, [])
        self.assertIsNone(HDRezkaCache(plugin.profile).get_post_translation('92422'))
        # silent site-default resolve: full listing, no choice stored
        labels = [item.label for _, _, item, _ in xbmcplugin.ADDED[1:]]
        self.assertEqual(labels, ['1 серия (Сезон 1)', '2 серия (Сезон 1)', '3 серия (Сезон 2)'])

    def test_dialog_on_cache_miss_when_select(self):
        plugin = make_plugin(series_routes(), {'translator': 'select'})
        plugin.show('/series/x.html', False, None)
        self.assertEqual(len(xbmcgui.Dialog.select_calls), 1)
        self.assertEqual(HDRezkaCache(plugin.profile).get_post_translation('92422'), '111')

    def test_ragged_episode_lists_do_not_crash(self):
        ragged = {
            'episodes': (
                '<ul class="b-simple_episodes__list clearfix">'
                '<li data-id="11" data-season_id="1" data-episode_id="1">1 серия</li>'
                '<li data-id="12" data-season_id="1" data-episode_id="2">2 серия</li>'
                '<li data-id="13" data-season_id="2">3 серия без эпизода</li>'
                '</ul>'
            )
        }
        plugin = make_plugin({
            ('GET', '/series/x.html'): FakeResponse(text=series_page()),
            ('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=ragged),
        })
        cached(plugin, '92422', '56')
        plugin.show('/series/x.html', False, None)
        labels = [item.label for _, _, item, _ in xbmcplugin.ADDED[1:]]
        self.assertEqual(labels, ['1 серия (Сезон 1)', '2 серия (Сезон 1)'])

    def test_garbage_translator_id_falls_back_to_default(self):
        page = (
            '<div class="b-content__main">'
            '<img itemprop="image" src="https://statichdrezka.ac/i/x.jpg">'
            '<h1>Тест</h1>'
            '</div>'
            '<input id="post_id" value="92422">'
            '<div id="simple-episodes-tabs"><ul>'
            '<li data-id="11" data-season_id="1" data-episode_id="1">1 серия</li>'
            '</ul></div>'
            '<script>var x = sof.tv.initCDNSeriesEvents(92422, прячься, {ajax: 1});</script>'
        )
        plugin = make_plugin({('GET', '/series/x.html'): FakeResponse(text=page)})
        plugin.show('/series/x.html', False, None)
        _, url, _, _ = xbmcplugin.ADDED[0]
        self.assertEqual(router.parse_uri(url).get('idt'), '0')


class SeriesAtlTest(unittest.TestCase):
    def run_atl_show(self, **settings):
        opts = {'use_atl_names': 'true'}
        opts.update(settings)
        plugin = make_plugin(series_routes(), opts)
        plugin.show('/series/x.html', True, None)
        return plugin

    def test_atl_labels(self):
        self.run_atl_show()
        labels = [item.label for _, _, item, _ in xbmcplugin.ADDED[1:]]
        self.assertEqual(labels, [
            'Тестовый сериал.s01e01',
            'Тестовый сериал.s01e02',
            'Тестовый сериал.s02e03',
        ])

    def test_atl_urls_and_playable(self):
        self.run_atl_show()
        first = xbmcplugin.ADDED[0]
        self.assertIn('Перевод', first[2].label)
        for _, url, item, is_folder in xbmcplugin.ADDED[1:]:
            self.assertFalse(is_folder)
            self.assertEqual(item._properties.get('IsPlayable'), 'true')
            self.assertIn('strm=1', url)
            self.assertIn('idt=111', url)
        self.assertIn('season_id=2', xbmcplugin.ADDED[3][1])
        self.assertIn('episode_id=3', xbmcplugin.ADDED[3][1])

    def test_translator_item_present_no_dialog(self):
        self.run_atl_show()
        self.assertEqual(len(xbmcplugin.ADDED), 4)
        self.assertEqual(xbmcgui.Dialog.select_calls, [])

    def test_cached_translator_baked(self):
        plugin = make_plugin(series_routes(), {'use_atl_names': 'true'})
        cached(plugin, '92422', '56')
        plugin.show('/series/x.html', True, None)
        self.assertIn('idt=56', xbmcplugin.ADDED[1][1])


class MovieTest(unittest.TestCase):
    def movie_plugin(self, routes_extra=None, settings=None):
        routes = {('GET', '/films/x.html'): FakeResponse(text=movie_page())}
        routes.update(routes_extra or {})
        return make_plugin(routes, settings)

    def test_quality_listing_when_select(self):
        plugin = self.movie_plugin(
            {('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=MOVIE_AJAX_OK)},
            {'quality': 'select'})
        cached(plugin, '777', '56')
        plugin.show('/films/x.html', False, None)
        self.assertEqual(len(xbmcplugin.ADDED), 3)
        for _, url, item, is_folder in xbmcplugin.ADDED[1:]:
            self.assertFalse(is_folder)
            self.assertIn('mode=play', url)

    def test_direct_play_with_quality(self):
        plugin = self.movie_plugin(
            {('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=MOVIE_AJAX_OK)})
        cached(plugin, '777', '56')
        plugin.show('/films/x.html', False, None)
        self.assertEqual(len(xbmcplugin.RESOLVED), 1)
        handle, succeeded, item = xbmcplugin.RESOLVED[0]
        self.assertTrue(succeeded)
        self.assertIn('x720.mp4', item.path)

    def test_uses_cached_translator(self):
        plugin = self.movie_plugin(
            {('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=MOVIE_AJAX_OK)})
        cached(plugin, '777', '56')
        plugin.show('/films/x.html', False, None)
        posted = [c for c in plugin.make_response.calls if c['method'] == 'POST'][0]
        self.assertEqual(posted['data']['translator_id'], '56')
        self.assertEqual(posted['data']['action'], 'get_movie')

    def test_fallback_to_embedded_streams(self):
        plugin = self.movie_plugin(
            {('POST', '/ajax/get_cdn_series/'): FakeResponse(json_exc=ValueError('no'))})
        cached(plugin, '777', '56')
        plugin.show('/films/x.html', False, None)
        self.assertEqual(len(xbmcplugin.RESOLVED), 1)

    def test_missing_streams_block_returns_quietly(self):
        page = (
            '<div class="b-content__main">'
            '<img itemprop="image" src="https://statichdrezka.ac/i/y.jpg">'
            '<h1>Тестовый фильм</h1>'
            '<ul id="translators-list">' + TRANSLATORS_DIV + '</ul>'
            '</div>'
            '<input id="post_id" value="777">'
        )
        plugin = self.movie_plugin({
            ('GET', '/films/x.html'): FakeResponse(text=page),
            ('POST', '/ajax/get_cdn_series/'): FakeResponse(json_exc=ValueError('no')),
        })
        cached(plugin, '777', '56')
        plugin.show('/films/x.html', False, None)
        self.assertEqual(xbmcplugin.RESOLVED, [])

    def test_atl_setting_does_not_force_movies(self):
        plugin = self.movie_plugin(
            {('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=MOVIE_AJAX_OK)},
            {'use_atl_names': 'true', 'quality': 'select'})
        cached(plugin, '777', '56')
        plugin.show('/films/x.html', True, None)
        self.assertEqual(xbmcplugin.RESOLVED, [])
        rows = xbmcplugin.ADDED[1:]
        self.assertEqual(len(rows), 2)
        for _, url, _, is_folder in rows:
            self.assertFalse(is_folder)
            self.assertIn('mode=play', url)

    def test_dialog_on_cache_miss_even_in_atl(self):
        plugin = self.movie_plugin(
            {('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=MOVIE_AJAX_OK)},
            {'use_atl_names': 'true'})
        plugin.show('/films/x.html', True, None)
        self.assertEqual(len(xbmcgui.Dialog.select_calls), 1)


class AnubisTest(unittest.TestCase):
    def run_solve(self, html):
        routes = {('GET', '/.within.website/x/cmd/anubis/api/pass-challenge'): FakeResponse(text='{}')}
        plugin = make_plugin(routes)
        self.assertTrue(plugin.solve_anubis(html, '/films/x.html'))
        self.assertTrue(plugin.make_response.calls)

    def test_solves_div_challenge(self):
        self.run_solve(ANUBIS_HTML)

    def test_solves_script_challenge(self):
        html = ANUBIS_HTML.replace('<div id="anubis_challenge">', '<script id="anubis_challenge" type="application/json">').replace('</div>', '</script>')
        self.run_solve(html)

    def test_missing_challenge_is_false(self):
        plugin = make_plugin()
        self.assertFalse(plugin.solve_anubis('<html>no challenge</html>', '/films/x.html'))
        self.assertEqual(plugin.make_response.calls, [])


if __name__ == '__main__':
    unittest.main()
