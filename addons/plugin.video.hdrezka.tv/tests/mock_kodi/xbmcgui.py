# tests/mock_kodi/xbmcgui.py
"""Minimal stub of xbmcgui: ListItem, Dialog, Keyboard helpers."""

NOTIFICATION_INFO = 1
NOTIFICATION_WARNING = 2
NOTIFICATION_ERROR = 3

ICON_OVERLAY_WATCHED = 1


class InfoTagVideo:
    def __init__(self):
        self._values = {}

    def setSeason(self, value):
        self._values['season'] = value

    def setEpisode(self, value):
        self._values['episode'] = value

    def setMediaType(self, value):
        self._values['mediatype'] = value

    def setTitle(self, value):
        self._values['title'] = value

    def setYear(self, value):
        self._values['year'] = value

    def setPlaycount(self, value):
        self._values['playcount'] = value


class ListItem:
    def __init__(self, label='', label2='', path=''):
        self.label = label
        self.label2 = label2
        self.path = path
        self._art = {}
        self._info = {}
        self._properties = {}
        self._context = []
        self._subtitles = []
        self._tag = InfoTagVideo()

    def setArt(self, art):
        self._art.update(art)

    def setInfo(self, type, infoLabels):
        self._info.update(infoLabels)

    def setProperty(self, key, value):
        self._properties[key] = value

    def getProperty(self, key):
        return self._properties.get(key, '')

    def addContextMenuItems(self, items):
        self._context.extend(items)

    def setSubtitles(self, subtitles):
        self._subtitles = list(subtitles)

    def getVideoInfoTag(self):
        return self._tag

    def getLabel(self):
        return self.label

    def getPath(self):
        return self.path


class Dialog:
    select_result = 0
    select_calls = []
    notifications = []
    oks = []

    def select(self, heading, choices):
        Dialog.select_calls.append((heading, list(choices)))
        return Dialog.select_result

    def notification(self, heading, message, icon=0, time=5000, sound=True):
        Dialog.notifications.append((heading, message))

    def ok(self, heading, message):
        Dialog.oks.append((heading, message))


class Keyboard:
    confirmed = True
    text = ''

    def __init__(self):
        pass

    def setDefault(self, value):
        pass

    def setHeading(self, value):
        pass

    def doModal(self):
        pass

    def isConfirmed(self):
        return Keyboard.confirmed

    def getText(self):
        return Keyboard.text


def reset():
    Dialog.select_result = 0
    del Dialog.select_calls[:]
    del Dialog.notifications[:]
    del Dialog.oks[:]
