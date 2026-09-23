# tests/test_quality_play.py
import unittest

import support
from support import (
    GET_STREAM_JSON, FakeResponse, make_plugin, xbmcaddon, xbmcgui, xbmcplugin,
)
from cache import HDRezkaCache

STREAMS = [('1080p', 1080, 'http://cdn/x1080.mp4'), ('720p', 720, 'http://cdn/x720.mp4')]


class SelectQualityTest(unittest.TestCase):
    def test_concrete_quality_match(self):
        plugin = make_plugin()
        plugin.select_quality(list(STREAMS), 't', 'img')
        self.assertEqual(len(xbmcplugin.RESOLVED), 1)
        self.assertIn('x720.mp4', xbmcplugin.RESOLVED[0][2].path)

    def test_strm_forces_best_on_select(self):
        plugin = make_plugin({}, {'quality': 'select'})
        plugin.select_quality(list(STREAMS), 't', 'img', None, '1')
        self.assertIn('x1080.mp4', xbmcplugin.RESOLVED[0][2].path)

    def test_resolved_item_carries_title(self):
        plugin = make_plugin()
        plugin.select_quality(list(STREAMS), 'MyTitle', 'img')
        self.assertEqual(xbmcplugin.RESOLVED[0][2]._info.get('title'), 'MyTitle')

    def test_resolved_title_strips_year(self):
        plugin = make_plugin()
        plugin.select_quality(list(STREAMS), 'Film (2025)', 'img')
        self.assertEqual(xbmcplugin.RESOLVED[0][2]._info.get('title'), 'Film')


class SaveSessionTest(unittest.TestCase):
    def real_call(self, response_cookies):
        plugin = make_plugin()
        del plugin.make_response
        response = FakeResponse(text='{}')
        response.cookies = response_cookies
        plugin.session.request = lambda *args, **kwargs: response
        plugin.make_response('GET', '/x')

    def test_saves_when_response_sets_cookies(self):
        from requests.cookies import RequestsCookieJar, create_cookie
        jar = RequestsCookieJar()
        jar.set_cookie(create_cookie('a', 'b', domain='example.com', path='/'))
        self.real_call(jar)
        self.assertIn((support.ADDON_ID, 'cookies'), xbmcaddon.STORE)

    def test_skips_when_no_cookies(self):
        self.real_call([])
        self.assertEqual(xbmcaddon.STORE.get((support.ADDON_ID, 'cookies')), '')

    def test_retries_dropped_connection_once(self):
        import requests as real_requests
        plugin = make_plugin()
        del plugin.make_response
        ok_response = FakeResponse(text='{}')
        ok_response.cookies = []
        attempts = []

        def flaky(*args, **kwargs):
            attempts.append(1)
            if len(attempts) == 1:
                raise real_requests.exceptions.ConnectionError('dropped')
            return ok_response

        plugin.session.request = flaky
        self.assertIs(plugin.make_response('GET', '/x'), ok_response)
        self.assertEqual(len(attempts), 2)

    def test_gives_up_after_second_failure(self):
        import requests as real_requests
        plugin = make_plugin()
        del plugin.make_response

        def always_down(*args, **kwargs):
            raise real_requests.exceptions.ConnectionError('dropped')

        plugin.session.request = always_down
        with self.assertRaises(real_requests.exceptions.ConnectionError):
            plugin.make_response('GET', '/x')

    def test_retries_broken_chunks(self):
        import requests as real_requests
        plugin = make_plugin()
        del plugin.make_response
        ok_response = FakeResponse(text='{}')
        ok_response.cookies = []
        attempts = []

        def flaky(*args, **kwargs):
            attempts.append(1)
            if len(attempts) == 1:
                raise real_requests.exceptions.ChunkedEncodingError('cut')
            return ok_response

        plugin.session.request = flaky
        self.assertIs(plugin.make_response('GET', '/x'), ok_response)
        self.assertEqual(len(attempts), 2)

    def test_select_lists_qualities(self):
        plugin = make_plugin({}, {'quality': 'select'})
        plugin.select_quality(list(STREAMS), 't', 'img')
        self.assertEqual(len(xbmcplugin.ADDED), 2)
        self.assertEqual(xbmcplugin.RESOLVED, [])
        for _, url, item, is_folder in xbmcplugin.ADDED:
            self.assertFalse(is_folder)
            self.assertIn('mode=play', url)


class PlayTest(unittest.TestCase):
    def test_resolves_with_props(self):
        plugin = make_plugin()
        plugin.play('http://cdn/x.mp4', None, {'post_id': '1', 'season': '1'})
        handle, succeeded, item = xbmcplugin.RESOLVED[0]
        self.assertTrue(succeeded)
        self.assertEqual(item.path, 'http://cdn/x.mp4')
        self.assertEqual(item.getProperty('addon_id'), 'plugin.video.hdrezka.tv')
        self.assertEqual(item.getProperty('post_id'), '1')

    def test_no_props_for_movies(self):
        plugin = make_plugin()
        plugin.play('http://cdn/x.mp4')
        item = xbmcplugin.RESOLVED[0][2]
        self.assertEqual(item.getProperty('addon_id'), '')


class PlayEpisodeTest(unittest.TestCase):
    def run_episode(self, settings=None):
        routes = {('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=GET_STREAM_JSON)}
        plugin = make_plugin(routes, settings)
        HDRezkaCache(plugin.profile).set_post_translation('9', '56')
        plugin.play_episode('/series/x.html', '11', '1', '2', 't', 'img', '111', '1', '9')
        return plugin

    def test_cached_translator_overrides_url(self):
        plugin = self.run_episode()
        posted = plugin.make_response.calls[0]['data']
        self.assertEqual(posted['translator_id'], '56')
        self.assertEqual(posted['season'], '1')
        self.assertEqual(posted['episode'], '2')

    def test_strm_resolves_best(self):
        plugin = self.run_episode({'quality': 'select'})
        handle, succeeded, item = xbmcplugin.RESOLVED[0]
        self.assertTrue(succeeded)
        self.assertIn('e720.mp4', item.path)


class MainRoutesTest(unittest.TestCase):
    def test_dispatch(self):
        plugin = make_plugin()
        seen = []
        plugin.play = lambda url: seen.append(('play', url))
        plugin.show = lambda uri, atl=False, strm=None: seen.append(('show', uri, atl, strm))
        plugin.select_translator_item = lambda uri, via=None, atl=None, strm=None: seen.append(('translator', uri))
        plugin.main('?mode=show&uri=%2Fseries%2Fx.html&atl=true')
        plugin.main('?mode=select_translator&uri=%2Fseries%2Fx.html')
        plugin.main('?mode=play&url=http%3A%2F%2Fcdn%2Fx.mp4')
        self.assertIn(('show', '/series/x.html', True, None), seen)
        self.assertIn(('translator', '/series/x.html'), seen)
        self.assertIn(('play', 'http://cdn/x.mp4'), seen)

    def test_play_episode_without_title(self):
        routes = {('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=GET_STREAM_JSON)}
        plugin = make_plugin(routes)
        plugin.main('?mode=play_episode&url=%2Fseries%2Fx.html&post_id=11&season_id=1&episode_id=2&image=img&idt=111')
        self.assertEqual(len(xbmcplugin.RESOLVED), 1)


if __name__ == '__main__':
    unittest.main()
