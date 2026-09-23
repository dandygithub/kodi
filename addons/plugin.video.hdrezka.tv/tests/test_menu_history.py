# tests/test_menu_history.py
import unittest

import support
from support import FakeResponse, continue_page, make_plugin, xbmc, xbmcgui, xbmcplugin
import SearchHistory as history_module


class MenuTest(unittest.TestCase):
    def test_continue_entry_present(self):
        plugin = make_plugin()
        plugin.menu()
        labels = [item.label for _, _, item, _ in xbmcplugin.ADDED]
        self.assertEqual(len(labels), 8)
        self.assertIn('Продолжить просмотр', labels[-1])
        self.assertIn('mode=continue', xbmcplugin.ADDED[-1][1])


class HistoryTest(unittest.TestCase):
    def test_lists_reversed(self):
        plugin = make_plugin()
        history_module.add_to_history('один')
        history_module.add_to_history('два')
        plugin.history()
        labels = [item.label for _, _, item, _ in xbmcplugin.ADDED]
        self.assertEqual(labels, ['два', 'один'])
        menu = xbmcplugin.ADDED[0][2]._context
        self.assertEqual(len(menu), 1)
        self.assertIn('Удалить из истории', menu[0][0])
        self.assertIn('history_delete', menu[0][1])

    def test_delete_history(self):
        plugin = make_plugin()
        history_module.add_to_history('мусор')
        plugin.delete_history('мусор')
        self.assertEqual(history_module.get_history(), [])
        self.assertEqual(xbmcgui.Dialog.notifications[0][1], 'Успешно удалено из истории')
        self.assertIn('Container.Refresh()', xbmc.EXECUTED)


class ContinuesTest(unittest.TestCase):
    def run_continues(self, settings=None):
        routes = {('GET', '/continue/'): FakeResponse(text=continue_page())}
        plugin = make_plugin(routes, settings)
        plugin.continues()
        return plugin

    def test_listing(self):
        self.run_continues()
        self.assertEqual(len(xbmcplugin.ADDED), 2)
        serial = xbmcplugin.ADDED[0]
        movie = xbmcplugin.ADDED[1]
        self.assertIn('[s1e5', serial[2].label)
        self.assertIn('новых 3', serial[2].label)
        self.assertTrue(serial[3])
        self.assertFalse(movie[3])
        self.assertIn('i/200.jpg', serial[2]._art['thumb'])
        menu = serial[2]._context
        self.assertEqual(len(menu), 2)
        self.assertIn('continue_delete', menu[0][1])
        self.assertIn('id=555', menu[0][1])
        self.assertIn('Выбрать озвучку', menu[1][0])
        self.assertIn('select_translator', menu[1][1])

    def test_cached_name_overrides_site_translate(self):
        from cache import HDRezkaCache
        routes = {('GET', '/continue/'): FakeResponse(text=continue_page())}
        plugin = make_plugin(routes)
        HDRezkaCache(plugin.profile).set_post_translation('200', '56', 'Дубляж')
        plugin.continues()
        self.assertIn('Дубляж', xbmcplugin.ADDED[0][2].label)

    def test_delete_continue(self):
        routes = {('POST', '/engine/ajax/cdn_saves_remove.php'): FakeResponse(text='{}')}
        plugin = make_plugin(routes)
        plugin.delete_continue('555')
        posted = plugin.make_response.calls[0]
        self.assertEqual(posted['data'], {'id': '555'})
        self.assertEqual(xbmcgui.Dialog.notifications[0][1], 'Успешно удалено из Продолжить просмотр')
        self.assertIn('Container.Refresh()', xbmc.EXECUTED)


if __name__ == '__main__':
    unittest.main()
