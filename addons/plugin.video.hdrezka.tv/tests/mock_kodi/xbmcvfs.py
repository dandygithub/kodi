# tests/mock_kodi/xbmcvfs.py
"""Minimal stub of xbmcvfs: translatePath is a passthrough in tests."""


def translatePath(path):
    return path


def exists(path):
    import os
    return os.path.exists(path)


def mkdirs(path):
    import os
    os.makedirs(path, exist_ok=True)
