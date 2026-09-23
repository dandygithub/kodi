import unittest

import support  # noqa: F401  (path wiring only)
from support import FakeResponse, FakeTransport, make_plugin

from cache import HDRezkaCache


BUBBLE_HTML = (
    '<div class="b-content__bubble_text">Описание фильма</div>'
    '<div class="b-content__bubble_rating"><span class="label">Рейтинг:</span> <b>7.5</b></div>'
    '<div class="b-content__bubble_rates">'
    '<span class="imdb">IMDb: <b>7.1</b></span> <span class="kp">KP: <b>6.9</b></span>'
    '</div>'
)


class BubbleCacheTest(unittest.TestCase):
    def test_miss_parses_and_second_call_hits_cache(self):
        routes = {('POST', '/engine/ajax/quick_content.php'): FakeResponse(text=BUBBLE_HTML)}
        plugin = make_plugin(routes, {'show_description': 'true'})
        first = plugin.get_item_additional_info('1')
        self.assertEqual(first['rating']['site'], '7.5')
        self.assertEqual(len(plugin.make_response.calls), 1)
        plugin.make_response = FakeTransport({})
        second = plugin.get_item_additional_info('1')
        self.assertEqual(second, first)
        self.assertEqual(plugin.make_response.calls, [])

    def test_stale_entry_refetches(self):
        routes = {('POST', '/engine/ajax/quick_content.php'): FakeResponse(text=BUBBLE_HTML)}
        plugin = make_plugin(routes, {'show_description': 'true'})
        plugin.get_item_additional_info('1')
        cache = HDRezkaCache(plugin.profile)
        cache.conn.execute("UPDATE bubbles SET updated = 0 WHERE post_id = '1'")
        cache.conn.commit()
        plugin.make_response = FakeTransport(routes)
        info = plugin.get_item_additional_info('1')
        self.assertEqual(info['rating']['imdb'], '7.1')
        self.assertEqual(len(plugin.make_response.calls), 1)

    def test_write_purges_expired(self):
        routes = {('POST', '/engine/ajax/quick_content.php'): FakeResponse(text=BUBBLE_HTML)}
        plugin = make_plugin(routes, {'show_description': 'true'})
        cache = HDRezkaCache(plugin.profile)
        cache.set_bubble('old', {'description': 'x'}, 60)
        cache.conn.execute("UPDATE bubbles SET updated = 0 WHERE post_id = 'old'")
        cache.conn.commit()
        cache.set_bubble('fresh', {'description': 'y'}, 60)
        plugin.get_item_additional_info('1')
        self.assertIsNone(cache.get_bubble('old', 60))
        self.assertIsNotNone(cache.get_bubble('fresh', 60))
        self.assertIsNotNone(cache.get_bubble('1', 60))


if __name__ == '__main__':
    unittest.main()
