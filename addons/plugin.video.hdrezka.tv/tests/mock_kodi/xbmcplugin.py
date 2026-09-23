# tests/mock_kodi/xbmcplugin.py
"""Minimal stub of xbmcplugin recording directory/resolve calls."""

SORT_METHOD_TITLE = 1
SORT_METHOD_EPISODE = 2

ADDED = []
RESOLVED = []
CONTENT = []
END_OF_DIRECTORY = []
END_UPDATE = []


def addDirectoryItem(handle, url, listitem, isFolder=True):
    ADDED.append((handle, url, listitem, isFolder))
    return True


def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
    END_OF_DIRECTORY.append((handle, succeeded))
    END_UPDATE.append(updateListing)


def setResolvedUrl(handle, succeeded, listitem):
    RESOLVED.append((handle, succeeded, listitem))


def setContent(handle, content):
    CONTENT.append((handle, content))


def reset():
    del ADDED[:]
    del RESOLVED[:]
    del CONTENT[:]
    del END_OF_DIRECTORY[:]
    del END_UPDATE[:]
