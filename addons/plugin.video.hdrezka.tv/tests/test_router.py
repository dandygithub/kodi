# tests/test_router.py
import unittest

import support
from support import router


class BuildUriTest(unittest.TestCase):
    def test_skips_falsy_values(self):
        uri = router.build_uri('show', uri='/series/x.html', atl=None, strm='')
        self.assertNotIn('atl', uri)
        self.assertNotIn('strm', uri)
        self.assertIn('mode=show', uri)

    def test_keeps_truthy_values(self):
        uri = router.build_uri('play_episode', post_id='11', strm='1')
        self.assertIn('post_id=11', uri)
        self.assertIn('strm=1', uri)

    def test_roundtrip(self):
        uri = router.build_uri('show', uri='/series/x.html', atl='true')
        params = router.parse_uri(uri)
        self.assertEqual(params, {'mode': 'show', 'uri': '/series/x.html', 'atl': 'true'})


class NormalizeUriTest(unittest.TestCase):
    def test_keeps_path_only(self):
        self.assertEqual(router.normalize_uri('https://rezka.fi/series/x.html'), '/series/x.html')


if __name__ == '__main__':
    unittest.main()
