# tests/mock_kodi/xbmcaddon.py
"""Minimal stub of xbmcaddon with a per-test settings store."""

STORE = {}
STRINGS = {}
PROFILE_DIR = ''
ADDON_PATH = ''
PATHS = {}


class Addon:
    def __init__(self, addon_id='plugin.video.hdrezka.tv'):
        self._id = addon_id

    def getSetting(self, key):
        return STORE.get((self._id, key), '')

    def getSettingBool(self, key):
        return str(self.getSetting(key)).lower() == 'true'

    def setSetting(self, key, value):
        STORE[(self._id, key)] = value

    def getLocalizedString(self, string_id):
        return STRINGS.get(string_id, '')

    def getAddonInfo(self, key):
        if key == 'id':
            return self._id
        if key == 'profile':
            return PROFILE_DIR
        if key == 'path':
            return PATHS.get(self._id, ADDON_PATH)
        if key == 'icon':
            return 'icon.png'
        if key == 'name':
            return 'Hdrezka.tv'
        return ''


def reset():
    STORE.clear()
    STRINGS.clear()
