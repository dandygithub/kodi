# tests/run_all.py
"""Run the whole hdrezka test suite:  python tests/run_all.py  (from repo root or addon dir)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_router
import test_helpers
import test_cache
import test_bubble_cache
import test_library_urls
import test_voidboost
import test_actions
import test_translators
import test_show
import test_index
import test_quality_play
import test_menu_history
import test_player


def suite():
    loader = unittest.TestLoader()
    result = unittest.TestSuite()
    for module in (test_router, test_helpers, test_cache, test_bubble_cache,
                   test_library_urls,
                   test_voidboost,
                   test_actions, test_translators, test_show, test_index,
                   test_quality_play, test_menu_history, test_player):
        result.addTests(loader.loadTestsFromModule(module))
    return result


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    outcome = runner.run(suite())
    sys.exit(0 if outcome.wasSuccessful() else 1)
