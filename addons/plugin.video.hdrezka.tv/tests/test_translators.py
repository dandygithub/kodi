# tests/test_translators.py
import unittest

import support
from support import (
    EPISODES_JSON, FakeResponse, make_plugin, series_page, xbmcgui, xbmc, xbmcplugin,
)
from cache import HDRezkaCache


def series_plugin(idt_posts=None, **settings):
    routes = {('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=EPISODES_JSON)}
    plugin = make_plugin(routes, settings)
    if idt_posts:
        cache = HDRezkaCache(plugin.profile)
        for post_id, translator_id in idt_posts.items():
            cache.set_post_translation(post_id, translator_id)
    return plugin


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.plugin = make_plugin()

    def test_titles_ids_premium(self):
        titles, ids, directors, premium, active = self.plugin._parse_translators(series_page())
        self.assertEqual(ids, ['111', '56', '1', '376'])
        self.assertIn('HDrezka Studio', titles[0])
        self.assertEqual(premium, [True, False, False, True])

    def test_flag_image_suffix(self):
        titles, ids, directors, premium, active = self.plugin._parse_translators(series_page())
        self.assertIn('(Украинский)', titles[3])

    def test_missing_list_is_nones(self):
        self.assertEqual(self.plugin._parse_translators('<div>nothing</div>'), (None, None, None, None, None))

    def test_active_translator_found(self):
        titles, ids, directors, premium, active = self.plugin._parse_translators(series_page())
        self.assertEqual(active, '111')

    def test_active_missing_is_none(self):
        page = series_page(translators='<li title="One" class="b-translator__item" data-translator_id="7">One</li>')
        result = self.plugin._parse_translators(page)
        self.assertIsNone(result[4])

    def test_li_without_title_does_not_crash(self):
        page = series_page(translators=(
            '<li class="b-translator__item" data-translator_id="7">NoTitle</li>'
            '<li title="Two" class="b-translator__item" data-translator_id="8">Two</li>'
        ))
        titles, ids, directors, premium, active = self.plugin._parse_translators(page)
        self.assertEqual(ids, ['7', '8'])
        self.assertEqual(premium, [False])


class CachedTest(unittest.TestCase):
    def setUp(self):
        self.plugin = make_plugin()

    def test_miss(self):
        self.assertIsNone(self.plugin._get_cached_translator('92422', ['111']))

    def test_hit(self):
        HDRezkaCache(self.plugin.profile).set_post_translation('92422', '56')
        self.assertEqual(self.plugin._get_cached_translator('92422', ['111', '56']), '56')

    def test_stale_id_ignored(self):
        HDRezkaCache(self.plugin.profile).set_post_translation('92422', '999')
        self.assertIsNone(self.plugin._get_cached_translator('92422', ['111', '56']))


class SilentSelectTest(unittest.TestCase):
    def test_uses_cached_translator_and_no_dialog(self):
        plugin = series_plugin({'92422': '56'})
        playlist, idt, subtitles = plugin.select_translator(
            series_page(), ['old'], '92422', '/series/x.html', '111', 'get_episodes')
        posted = plugin.make_response.calls[0]['data']
        self.assertEqual(posted['translator_id'], '56')
        self.assertEqual(posted['action'], 'get_episodes')
        self.assertEqual(idt, '56')
        self.assertTrue(playlist)
        self.assertEqual(xbmcgui.Dialog.select_calls, [])

    def test_falls_back_to_site_default(self):
        plugin = series_plugin()
        playlist, idt, subtitles = plugin.select_translator(
            series_page(), ['old'], '92422', '/series/x.html', '111', 'get_episodes')
        self.assertEqual(plugin.make_response.calls[0]['data']['translator_id'], '111')
        self.assertEqual(idt, '111')

    def test_request_fault_returns_input(self):
        plugin = make_plugin({('POST', '/ajax/get_cdn_series/'): FakeResponse(json_exc=ValueError('no'))})
        tv_show, idt, subtitles = plugin.select_translator(
            series_page(), ['old'], '92422', '/series/x.html', '111', 'get_episodes')
        self.assertEqual((tv_show, idt, subtitles), (['old'], '111', None))


class DialogSelectTest(unittest.TestCase):
    def test_picks_and_saves(self):
        plugin = series_plugin()
        xbmcgui.Dialog.select_result = 2
        playlist, idt, subtitles = plugin.select_translator(
            series_page(), ['old'], '92422', '/series/x.html', '111', 'get_episodes', allow_dialog=True)
        self.assertEqual(idt, '1')
        posted = plugin.make_response.calls[-1]['data']
        self.assertEqual(posted['translator_id'], '1')
        cache = HDRezkaCache(plugin.profile)
        self.assertEqual(cache.get_post_translation('92422'), '1')
        self.assertEqual(len(xbmcgui.Dialog.select_calls), 1)

    def test_cancel_keeps_default_and_saves_nothing(self):
        plugin = series_plugin()
        xbmcgui.Dialog.select_result = -1
        playlist, idt, subtitles = plugin.select_translator(
            series_page(), ['old'], '92422', '/series/x.html', '111', 'get_episodes', allow_dialog=True)
        self.assertEqual(idt, '111')
        cache = HDRezkaCache(plugin.profile)
        self.assertIsNone(cache.get_post_translation('92422'))


class AnnotateTest(unittest.TestCase):
    def test_counts_premium_and_current(self):
        plugin = series_plugin({'92422': '56'})
        titles, ids, directors, premium, active = plugin._parse_translators(series_page())
        display = plugin._annotate_translators(titles, ids, directors, premium, '92422', '/series/x.html', '56')
        self.assertIn(' [3]', display[0])
        self.assertIn('Премиум', display[0])
        self.assertTrue(display[1].startswith('* '))
        self.assertNotIn('*', display[2])


class SelectItemTest(unittest.TestCase):
    def test_line_flow_saves_and_rebuilds_show(self):
        routes = {
            ('GET', '/series/x.html'): FakeResponse(text=series_page()),
            ('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=EPISODES_JSON),
            ('POST', '/ajax/send_watching/?t='): FakeResponse(json_data={'success': True}),
        }
        plugin = make_plugin(routes)
        xbmcgui.Dialog.select_result = 1
        plugin.select_translator_item('/series/x.html')
        cache = HDRezkaCache(plugin.profile)
        self.assertEqual(cache.get_post_translation('92422'), '56')
        self.assertEqual(cache.get_post_translation_name('92422'), 'Дубляж')
        pushed = [c for c in plugin.make_response.calls if c['uri'] == '/ajax/send_watching/?t=']
        self.assertEqual(len(pushed), 1)
        self.assertEqual(pushed[0]['data'], {'id': '92422', 'action': 'add', 'translator_id': '56'})
        labels = [item.label for _, _, item, _ in xbmcplugin.ADDED]
        self.assertIn('Перевод: Дубляж', labels[0])
        self.assertEqual(len(labels), 4)
        self.assertEqual(xbmcplugin.END_OF_DIRECTORY, [(1, True)])
        self.assertEqual(xbmcplugin.END_UPDATE, [False])
        nav = [c for c in xbmc.EXECUTED if 'Container.Update(' in c or 'Refresh' in c and 'busydialog' not in c]
        self.assertEqual(nav, [])

    def test_menu_flow_refreshes(self):
        routes = {
            ('GET', '/series/x.html'): FakeResponse(text=series_page()),
            ('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=EPISODES_JSON),
            ('POST', '/ajax/send_watching/?t='): FakeResponse(json_data={'success': True}),
        }
        plugin = make_plugin(routes)
        xbmcgui.Dialog.select_result = 1
        plugin.select_translator_item('/series/x.html', via='menu')
        cache = HDRezkaCache(plugin.profile)
        self.assertEqual(cache.get_post_translation('92422'), '56')
        self.assertIn('Container.Refresh()', xbmc.EXECUTED)
        self.assertEqual(xbmcplugin.ADDED, [])
        self.assertEqual(xbmcplugin.END_OF_DIRECTORY, [])

    def test_empty_response_retried_once(self):
        routes = {
            ('GET', '/series/x.html'): [
                FakeResponse(text=''),
                FakeResponse(text=series_page()),
                FakeResponse(text=series_page()),
            ],
            ('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=EPISODES_JSON),
            ('POST', '/ajax/send_watching/?t='): FakeResponse(json_data={'success': True}),
        }
        plugin = make_plugin(routes)
        xbmcgui.Dialog.select_result = 1
        plugin.select_translator_item('/series/x.html')
        cache = HDRezkaCache(plugin.profile)
        self.assertEqual(cache.get_post_translation('92422'), '56')
        self.assertEqual(len(xbmcplugin.ADDED), 4)
        self.assertEqual(xbmcplugin.END_OF_DIRECTORY, [(1, True)])
        self.assertEqual(xbmcplugin.END_UPDATE, [False])

    def test_cancel_rebuilds_without_saving(self):
        routes = {('GET', '/series/x.html'): FakeResponse(text=series_page())}
        plugin = make_plugin(routes)
        xbmcgui.Dialog.select_result = -1
        plugin.select_translator_item('/series/x.html')
        cache = HDRezkaCache(plugin.profile)
        self.assertIsNone(cache.get_post_translation('92422'))
        nav = [c for c in xbmc.EXECUTED if 'Container.Update(' in c or 'Refresh' in c]
        self.assertEqual(nav, [])
        # nested dialog cancels too (cached miss): row only, no episodes
        self.assertEqual(len(xbmcplugin.ADDED), 1)
        self.assertEqual(xbmcplugin.END_OF_DIRECTORY, [(1, True)])
        self.assertEqual(xbmcplugin.END_UPDATE, [False])

    def test_site_push_fault_keeps_cache(self):
        routes = {
            ('GET', '/series/x.html'): FakeResponse(text=series_page()),
            ('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=EPISODES_JSON),
            ('POST', '/ajax/send_watching/?t='): FakeResponse(json_exc=ValueError('no')),
        }
        plugin = make_plugin(routes)
        xbmcgui.Dialog.select_result = 1
        plugin.select_translator_item('/series/x.html')
        cache = HDRezkaCache(plugin.profile)
        self.assertEqual(cache.get_post_translation('92422'), '56')
        self.assertEqual(len(xbmcplugin.ADDED), 4)
        self.assertEqual(xbmcplugin.END_OF_DIRECTORY, [(1, True)])
        self.assertEqual(xbmcplugin.END_UPDATE, [False])
        nav = [c for c in xbmc.EXECUTED if 'Container.Update(' in c or 'Refresh' in c and 'busydialog' not in c]
        self.assertEqual(nav, [])

    def test_cancel_returns_without_saving(self):
        routes = {('GET', '/series/x.html'): FakeResponse(text=series_page())}
        plugin = make_plugin(routes)
        xbmcgui.Dialog.select_result = -1
        plugin.select_translator_item('/series/x.html')
        cache = HDRezkaCache(plugin.profile)
        self.assertIsNone(cache.get_post_translation('92422'))
        pushed = [c for c in plugin.make_response.calls if c['uri'] == '/ajax/send_watching/?t=']
        self.assertEqual(pushed, [])
        nav = [c for c in xbmc.EXECUTED if 'Refresh' in c]
        self.assertEqual(nav, [])

    def test_movie_dialog_marks_premium_without_counts(self):
        from support import movie_page
        routes = {
            ('GET', '/films/x.html'): FakeResponse(text=movie_page()),
            ('POST', '/ajax/send_watching/?t='): FakeResponse(json_data={'success': True}),
        }
        plugin = make_plugin(routes)
        plugin.select_translator_item('/films/x.html')
        choices = xbmcgui.Dialog.select_calls[0][1]
        self.assertTrue([c for c in choices if 'Премиум' in c])
        posts = [c for c in plugin.make_response.calls if c['method'] == 'POST']
        self.assertEqual([p['uri'] for p in posts],
                         ['/ajax/get_cdn_series/', '/ajax/send_watching/?t='])
        self.assertEqual(len(xbmcplugin.RESOLVED), 1)
        self.assertEqual(xbmcplugin.END_OF_DIRECTORY, [(1, True)])
        self.assertEqual(xbmcplugin.END_UPDATE, [False])

    def test_single_translator_shows_dialog(self):
        single = series_page(translators='<li title="One" class="b-translator__item" data-translator_id="7">One</li>')
        routes = {
            ('GET', '/series/x.html'): FakeResponse(text=single),
            ('POST', '/ajax/get_cdn_series/'): FakeResponse(json_data=EPISODES_JSON),
            ('POST', '/ajax/send_watching/?t='): FakeResponse(json_data={'success': True}),
        }
        plugin = make_plugin(routes)
        plugin.select_translator_item('/series/x.html')
        self.assertEqual(len(xbmcgui.Dialog.select_calls), 1)
        cache = HDRezkaCache(plugin.profile)
        self.assertEqual(cache.get_post_translation('92422'), '7')
        self.assertEqual(len(xbmcplugin.ADDED), 4)
        self.assertEqual(xbmcplugin.END_OF_DIRECTORY, [(1, True)])
        self.assertEqual(xbmcplugin.END_UPDATE, [False])


if __name__ == '__main__':
    unittest.main()
