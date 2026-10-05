import unittest

import support  # noqa: F401  (path wiring only)
import support as support_module
from support import EPISODES_JSON, FakeResponse, make_plugin, series_page, xbmcgui

from cache import HDRezkaCache


def series_routes():
    return {
        ('GET', '/series/x.html'): FakeResponse(text=series_page()),
        ('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=EPISODES_JSON),
    }


def episode_urls(plugin, atl_mode):
    plugin.show('/series/x.html', atl_mode, None)
    return [url for _, url, _, _ in support_module.xbmcplugin.ADDED[1:]]


class LibraryUrlsTest(unittest.TestCase):
    def test_atl_episode_urls_have_no_show_id(self):
        plugin = make_plugin(series_routes(), {'use_atl_names': 'true'})
        HDRezkaCache(plugin.profile).set_post_translation('92422', '56', 'Дубляж')
        urls = episode_urls(plugin, True)
        self.assertTrue(urls)
        for url in urls:
            self.assertNotIn('show_id', url)
            self.assertIn('strm=1', url)
            self.assertIn('idt=56', url)

    def test_interactive_episode_urls_have_no_show_id(self):
        plugin = make_plugin(series_routes())
        HDRezkaCache(plugin.profile).set_post_translation('92422', '111')
        urls = episode_urls(plugin, False)
        self.assertTrue(urls)
        for url in urls:
            self.assertNotIn('show_id', url)
            self.assertIn('idt=111', url)

    def test_translator_row_present_without_atl_flag(self):
        for settings, atl_mode in ((None, False), ({'use_atl_names': 'true'}, True)):
            plugin = make_plugin(series_routes(), settings)
            plugin.show('/series/x.html', atl_mode, None)
            _, url, item, is_folder = support_module.xbmcplugin.ADDED[0]
            self.assertTrue(is_folder)
            self.assertNotIn('atl=', url)
            self.assertIn('via=line', url)
            self.assertEqual(item._properties.get('IsPlayable'), 'false')
            support_module.xbmcplugin.reset()


class AtlTranslatorRouteTest(unittest.TestCase):
    def test_atl_line_route_never_dialogs(self):
        plugin = make_plugin(series_routes(), {'use_atl_names': 'true'})
        HDRezkaCache(plugin.profile).set_post_translation('92422', '56', 'Дубляж')
        plugin.select_translator_item('/series/x.html', via='line', atl='true')
        self.assertEqual(xbmcgui.Dialog.select_calls, [])
        self.assertEqual(xbmcgui.Dialog.notifications, [])
        labels = [item.label for _, _, item, _ in support_module.xbmcplugin.ADDED]
        self.assertIn('Тестовый сериал.s01e01', labels)
        self.assertEqual(support_module.xbmcplugin.END_OF_DIRECTORY, [(1, True)])
        self.assertEqual(support_module.xbmcplugin.END_UPDATE, [False])
        pushed = [c for c in plugin.make_response.calls if c['uri'] == '/ajax/send_watching/?t=']
        self.assertEqual(pushed, [])

    def test_interactive_line_rebuilds_show(self):
        routes = series_routes()
        routes[('POST', '/ajax/send_watching/?t=')] = FakeResponse(json_data={'success': True})
        plugin = make_plugin(routes)
        xbmcgui.Dialog.select_result = 1
        plugin.select_translator_item('/series/x.html', via='line')
        self.assertEqual(len(xbmcgui.Dialog.select_calls), 1)
        cache = HDRezkaCache(plugin.profile)
        self.assertEqual(cache.get_post_translation('92422'), '56')
        self.assertEqual(len(support_module.xbmcplugin.ADDED), 4)
        self.assertEqual(support_module.xbmcplugin.END_OF_DIRECTORY, [(1, True)])
        self.assertEqual(support_module.xbmcplugin.END_UPDATE, [False])
        nav = [c for c in support_module.xbmc.EXECUTED if 'Container.Update(' in c or 'Refresh' in c]
        self.assertEqual(nav, [])


if __name__ == '__main__':
    unittest.main()
