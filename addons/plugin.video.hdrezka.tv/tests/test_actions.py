# tests/test_actions.py
import unittest

import support
from support import FakeResponse, make_plugin, xbmcgui
import actions


class FakeConfigResponse(FakeResponse):
    def __init__(self, payload):
        super(FakeConfigResponse, self).__init__(text='{}')
        self._payload = payload
        self.ok = True
        self.status_code = 200

    def json(self):
        return self._payload


class ExternalConfigTest(unittest.TestCase):
    def test_updates_settings_with_timeout(self):
        plugin = make_plugin({}, {'external_config_url': 'http://cfg/x.json'})
        seen = {}
        real_get = actions.requests.get

        def fake_get(url, **kwargs):
            seen['url'] = url
            seen.update(kwargs)
            return FakeConfigResponse({'domain': 'x.test'})

        actions.requests.get = fake_get
        try:
            actions.external_config_update(plugin)
        finally:
            actions.requests.get = real_get
        self.assertEqual(seen['url'], 'http://cfg/x.json')
        self.assertEqual(seen['timeout'], 30)
        self.assertIn('User-Agent', seen['headers'])
        self.assertIn('proxies', seen)
        self.assertEqual(plugin.addon.getSetting('domain'), 'x.test')
        self.assertTrue(xbmcgui.Dialog.notifications)

    def test_failed_fetch_shows_ok(self):
        plugin = make_plugin({}, {'external_config_url': 'http://cfg/x.json'})
        real_get = actions.requests.get

        class BadResponse(FakeConfigResponse):
            def __init__(self):
                super(BadResponse, self).__init__({})
                self.ok = False
                self.status_code = 500

        actions.requests.get = lambda url, **kwargs: BadResponse()
        try:
            actions.external_config_update(plugin)
        finally:
            actions.requests.get = real_get
        self.assertTrue(xbmcgui.Dialog.oks)


if __name__ == '__main__':
    unittest.main()
