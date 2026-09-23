# tests/test_voidboost.py
"""Contract tests for the stream-block format our fixtures (and the site)
rely on: comma-separated [quality]http...mp4 blocks, correct pairing."""
import unittest

import support  # noqa: F401  (path wiring only)
from voidboost import parse_streams


class ParseTest(unittest.TestCase):
    def test_pairs_and_sorts_desc(self):
        streams = parse_streams('[720p] http://cdn/x720.mp4, [1080p] http://cdn/x1080.mp4')
        self.assertEqual(streams, [
            ('1080p', 1080, 'http://cdn/x1080.mp4'),
            ('720p', 720, 'http://cdn/x720.mp4'),
        ])

    def test_adjacent_blocks_pair_correctly(self):
        streams = parse_streams('[720p]http://cdn/x720.mp4[1080p]http://cdn/x1080.mp4')
        self.assertEqual(streams, [
            ('1080p', 1080, 'http://cdn/x1080.mp4'),
            ('720p', 720, 'http://cdn/x720.mp4'),
        ])

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_streams('no streams here')
        with self.assertRaises(ValueError):
            parse_streams('   ')


if __name__ == '__main__':
    unittest.main()
