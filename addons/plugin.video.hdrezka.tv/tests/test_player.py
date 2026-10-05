# tests/test_player.py
import unittest

import support
from support import FakeHdrezkaTV, FakeSession, default, xbmc, xbmcgui


def playing_item(**props):
    item = xbmcgui.ListItem('t')
    for key, value in props.items():
        item.setProperty(key, value)
    return item


class StartTest(unittest.TestCase):
    def setUp(self):
        support.reset_all()
        from HDRezkaPlayer import HDRezkaPlayer
        self.player = HDRezkaPlayer()

    def test_ignores_foreign_addon(self):
        self.player._playing_item = playing_item(addon_id='other.addon')
        self.player.onAVStarted()
        self.assertIsNone(self.player.current_video)

    def test_no_sleep_on_foreign_video(self):
        self.player._playing_item = playing_item(addon_id='other.addon')
        self.player.onAVStarted()
        self.assertEqual(xbmc.SLEEP_CALLS, [])

    def test_sleeps_for_own_video(self):
        self.player._playing_item = playing_item(addon_id='plugin.video.hdrezka.tv')
        self.player.onAVStarted()
        self.assertEqual(xbmc.SLEEP_CALLS, [1000])

    def test_ignores_missing_item(self):
        self.player._playing_item = None
        self.player.onAVStarted()
        self.assertIsNone(self.player.current_video)

    def test_accepts_own_item(self):
        self.player._playing_item = playing_item(
            addon_id='plugin.video.hdrezka.tv', post_id='11',
            translator_id='56', season='1', episode='2')
        self.player._total = 1000.0
        self.player.onAVStarted()
        video = self.player.current_video
        self.assertEqual(video['post_id'], '11')
        self.assertEqual(video['translator_id'], '56')
        self.assertEqual(video['season'], '1')
        self.assertEqual(video['episode'], '2')
        self.assertEqual(video['duration'], 1000.0)
        self.assertEqual(self.player.last_position, 0)


class SendTest(unittest.TestCase):
    def setUp(self):
        support.reset_all()
        from HDRezkaPlayer import HDRezkaPlayer
        self.player = HDRezkaPlayer()
        self.session = FakeSession()
        self.fake_tv = FakeHdrezkaTV(self.session)
        self._real = default.HdrezkaTV
        default.HdrezkaTV = lambda: self.fake_tv
        self.addCleanup(setattr, default, 'HdrezkaTV', self._real)
        self.player.current_video = {
            'post_id': '11', 'translator_id': '56', 'season': '1',
            'episode': '2', 'duration': 1000.0, 'start_time': 0,
        }
        self.player.last_position = 100.0

    def test_stopped_sends_position(self):
        self.player.onPlayBackStopped()
        posted = self.session.posts[0]
        self.assertIn('/ajax/send_save/', posted['url'])
        self.assertEqual(posted['data']['current_time'], 100.0)
        self.assertEqual(posted['data']['post_id'], '11')
        self.assertEqual(self.fake_tv.saved, 1)
        self.assertIsNone(self.player.current_video)

    def test_ended_sends_duration(self):
        self.player.onPlayBackEnded()
        posted = self.session.posts[0]
        self.assertEqual(posted['data']['current_time'], 1000.0)

    def test_empty_post_id_skipped(self):
        self.player.current_video['post_id'] = ''
        self.player.onPlayBackStopped()
        self.assertEqual(self.session.posts, [])
        self.assertIsNone(self.player.current_video)

    def test_pause_resume_flags(self):
        self.player._time = 42.0
        self.player.onPlayBackPaused()
        self.assertTrue(self.player.is_paused)
        self.assertEqual(self.player.last_position, 42.0)
        self.player.onPlayBackResumed()
        self.assertFalse(self.player.is_paused)


if __name__ == '__main__':
    unittest.main()
