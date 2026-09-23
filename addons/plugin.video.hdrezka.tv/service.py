# -*- coding: utf-8 -*-
# Background service: keeps HDRezkaPlayer alive to report watch progress
# to the site ("continue watching"). No UI here.

import xbmc

from helpers import log
from resources.lib.HDRezkaPlayer import HDRezkaPlayer


if __name__ == '__main__':
    player = HDRezkaPlayer()
    monitor = xbmc.Monitor()

    while not monitor.abortRequested():
        if player.current_video and not player.is_paused and player.isPlaying():
            try:
                player.last_position = player.getTime()
            except Exception as ex:
                log('service fault getTime ex: %s' % ex)
        if monitor.waitForAbort(10):
            break
