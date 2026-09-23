# tests/mock_kodi/xbmc.py
"""Minimal stub of the Kodi xbmc module for unit tests (no Kodi running)."""

LOGDEBUG = 0
LOGINFO = 1
LOGWARNING = 2
LOGERROR = 3
LOGFATAL = 4
LOGNONE = 5

LOG = []


def log(msg, level=LOGINFO):
    LOG.append((level, msg))


def executebuiltin(cmd):
    EXECUTED.append(cmd)


EXECUTED = []


def executeJSONRPC(request):
    JSONRPC_REQUESTS.append(request)
    return JSONRPC_RESPONSE


JSONRPC_REQUESTS = []
JSONRPC_RESPONSE = '{"jsonrpc": "2.0", "result": {}, "id": 1}'


def sleep(ms):
    SLEEP_CALLS.append(ms)


SLEEP_CALLS = []


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


class Monitor:
    def abortRequested(self):
        return False

    def waitForAbort(self, timeout):
        return True


class Player:
    def __init__(self):
        self._playing_item = None
        self._tag = InfoTagVideo()
        self._time = 0.0
        self._total = 0.0
        self._playing = False

    def getPlayingItem(self):
        return self._playing_item

    def getVideoInfoTag(self):
        return self._tag

    def getTime(self):
        return self._time

    def getTotalTime(self):
        return self._total

    def isPlaying(self):
        return self._playing

    def isPlayingVideo(self):
        return self._playing

    def onAVStarted(self):
        pass

    def onPlayBackStopped(self):
        pass

    def onPlayBackEnded(self):
        pass

    def onPlayBackPaused(self):
        pass

    def onPlayBackResumed(self):
        pass


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

    def getSeason(self):
        return self._values.get('season', -1)

    def getEpisode(self):
        return self._values.get('episode', -1)

    def getMediaType(self):
        return self._values.get('mediatype', '')

    def getTitle(self):
        return self._values.get('title', '')

    def getYear(self):
        return self._values.get('year', -1)

    def getDbId(self):
        return self._values.get('dbid', -1)

    def getDbId(self):
        return self._values.get('dbid', -1)

    def getMediaType(self):
        return self._values.get('mediatype', '')

    def getUniqueID(self, key):
        return self._values.get('uniqueid:' + key, '')


def reset():
    del LOG[:]
    del EXECUTED[:]
    del JSONRPC_REQUESTS[:]
    del SLEEP_CALLS[:]
