#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import utils
from api import YandexMusic, Album, Playlist, Track, Artist, get_image, get_artists, get_genre, get_duration


def get_track_list(album_id, tracks, info=None):
    track_list = []
    for number, track in enumerate(tracks, start=1):
        name = "[COLOR=FF00FFF0]%s[/COLOR] - %s" % (get_artists(track), track['title'])
        if not track['available']:
            name = '[COLOR=red][B]$[/B][/COLOR] ' + name
        li = xbmcgui.ListItem(name, thumbnailImage=get_image(track['ogImage']))
        info_labels = {
            'tracknumber': number,
            'artist': get_artists(track),
            'size': track['fileSize'],
            'duration': get_duration(track),
            'title': track['title']
        }
        if info:
            info_labels.update(**info)
        li.setInfo(type='music', infoLabels=info_labels)
        li.setProperty('IsPlayable', 'true')
        url = sys.argv[0] + '?mode=%s&album_id=%s&track_id=%s' % ('play', album_id, track['id'])
        track_list.append((url, li, False))
    return track_list


def get_album_list(albums):
    album_list = []
    for album in albums:
        li = xbmcgui.ListItem(
            "[COLOR=FF00FFF0]%s[/COLOR] - %s" % (get_artists(album), album['title']),
            thumbnailImage=get_image(album.get('coverUri'))
        )
        li.setInfo(
            type='music',
            infoLabels={
                'artist': get_artists(album),
                'album': album['title'],
                'year': album['year'],
                'genre': get_genre(album)
            }
        )

        url = sys.argv[0] + '?mode=%s&album_id=%s' % ('show_album', album['id'])
        album_list.append((url, li, True))
    return album_list


def get_playlist_list(playlists):
    playlist_list = []
    for playlist in playlists:
        li = xbmcgui.ListItem(
            "[COLOR=FF00FFF0]%s[/COLOR] - %s" % (playlist['owner']['name'], playlist['title']),
            thumbnailImage=get_image(playlist['ogImage'])
        )
        li.setInfo(
            type='music',
            infoLabels={
                'title': playlist['title'],
                'duration': get_duration(playlist)
            }
        )

        url = sys.argv[0] + '?mode=%s&owner_id=%s&playlist_id=%s' % ('show_playlist', playlist['uid'], playlist['kind'])
        playlist_list.append((url, li, True))
    return playlist_list


def get_artist_list(artists):
    playlist_list = []
    for artist in artists:
        li = xbmcgui.ListItem(
            "[COLOR=FF00FFF0]%s[/COLOR]" % (artist['name']),
            thumbnailImage=get_image(artist['ogImage'])
        )
        li.setInfo(
            type='music',
            infoLabels={
                'title': artist['name'],
                'genre': get_genre(artist['genres'], multiply=True),
                'rating': artist['ratings']['month']
            }
        )

        url = sys.argv[0] + '?mode=%s&artist_id=%s' % ('show_artist', artist['id'])
        playlist_list.append((url, li, True))
    return playlist_list


class MusicYandex:
    def __init__(self):
        self.id = 'plugin.audio.music.yandex'
        self.addon = xbmcaddon.Addon(self.id)
        self.settings = self._load_settings()

        self.api = YandexMusic()
        self.language = self.addon.getLocalizedString
        self.handle = int(sys.argv[1])
        self.patterns = self._load_patterns()

    def _load_settings(self):
        login = self.addon.getSetting('login')
        if not login:
            account = False
        else:
            account = {'owner': login.split('@')[0]}

        settings = {
            'icon': self.addon.getAddonInfo('icon'),
            'fanart': self.addon.getAddonInfo('fanart'),
            'account': account
        }
        return settings

    def _load_patterns(self):
        patterns = {
            'index': self.index,
            'my': self.my_music,
            'show_album': self.show_album,
            'show_playlist': self.show_playlist,
            'show_artist': self.show_artist,
            'play': self.play,
            'search': self.search,
        }
        return patterns

    def main(self):
        params = utils.get_parameters(sys.argv[2])
        method = self.patterns.get(params.get('mode'))
        if not method:
            return self.menu()
        return method(**params)

    def draw_menu(self, routers):
        for router in routers:
            url = sys.argv[0] + router['uri']
            item = xbmcgui.ListItem(router['name'], thumbnailImage=self.settings['icon'])
            item.setProperty('fanart_image', self.settings['fanart'])
            xbmcplugin.addDirectoryItem(self.handle, url, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def menu(self):
        routers = [
            {'name': '[COLOR=FF00FF00][Поиск][/COLOR]', 'uri': '?mode=search'},
            {'name': '[COLOR=FF00FFFF]Новые плейлисты[/COLOR]', 'uri': '?mode=index&what=new-playlists'},
            {'name': '[COLOR=FF00FFFF]Новые релизы[/COLOR]', 'uri': '?mode=index&what=new-releases'},
            {'name': '[COLOR=FF00FFFF]Чарт[/COLOR]', 'uri': '?mode=index&what=chart'}
        ]
        if self.settings['account']:
            routers.extend([
                {'name': '[COLOR=FF00FF00]Моя музыка[/COLOR]', 'uri': '?mode=my'},
            ])
        return self.draw_menu(routers)

    def show_playlist(self, owner_id, playlist_id, **kwargs):
        playlist = Playlist(owner_id, playlist_id)
        track_list = get_track_list(album_id=playlist.id, tracks=playlist.playlist['tracks'])

        xbmcplugin.addDirectoryItems(self.handle, track_list, len(track_list))
        xbmcplugin.setContent(self.handle, 'songs')
        xbmcplugin.endOfDirectory(self.handle)

    def show_album(self, album_id, **kwargs):
        album = Album(album_id)
        info = {'year': album.year, 'genre': album.genre}
        track_list = get_track_list(album_id=album_id, tracks=album.volumes[0], info=info)

        xbmcplugin.addDirectoryItems(self.handle, track_list, len(track_list))
        xbmcplugin.setContent(self.handle, 'songs')
        xbmcplugin.endOfDirectory(self.handle)

    def show_artist(self, artist_id, **kwargs):
        artist = Artist(artist_id)
        album_list = get_album_list(artist.albums)

        xbmcplugin.addDirectoryItems(self.handle, album_list, len(album_list))
        xbmcplugin.setContent(self.handle, 'albums')
        xbmcplugin.endOfDirectory(self.handle)

    def index(self, what, **kwargs):
        response = self.api.main(what)
        if what == 'new-playlists':
            ids = ('%s:%s' % (playlist['uid'], playlist['kind']) for playlist in response['newPlaylists'])
            items = get_playlist_list(self.api.get_playlists(ids))
        elif what == 'new-releases':
            items = get_album_list(self.api.get_albums(response['newReleases']))
        elif what == 'chart':
            items = get_track_list(response['chart']['uid'], response['chart']['tracks'])
        else:
            items = []

        xbmcplugin.addDirectoryItems(self.handle, items, len(items))
        xbmcplugin.setContent(self.handle, 'albums')
        xbmcplugin.endOfDirectory(self.handle, True)

    def my_music(self, filter_name=None, **kwargs):
        if not filter_name:
            routers = [
                {'name': '[COLOR=FF00FFFF]Треки[/COLOR]', 'uri': '?mode=my&filter_name=tracks'},
                {'name': '[COLOR=FF00FFFF]Альбомы[/COLOR]', 'uri': '?mode=my&filter_name=albums'},
                {'name': '[COLOR=FF00FFFF]Плейлисты[/COLOR]', 'uri': '?mode=my&filter_name=playlists'},
                {'name': '[COLOR=FF00FFFF]Исполнители[/COLOR]', 'uri': '?mode=my&filter_name=artists'},
            ]
            return self.draw_menu(routers)
        library = self.api.library(self.settings['account']['owner'], filter_name)
        if filter_name == 'tracks':
            items_list = get_track_list(album_id=library['owner']['uid'], tracks=library['tracks'])
            content_type = 'songs'
        elif filter_name == 'albums':
            items_list = get_album_list(library['albums'])
            content_type = 'albums'
        elif filter_name == 'playlists':
            items_list = get_playlist_list(library['bookmarks'])
            content_type = 'albums'
        elif filter_name == 'artists':
            items_list = get_artist_list(library['artists'])
            content_type = 'artists'
        else:
            items_list = []
            content_type = ''

        xbmcplugin.addDirectoryItems(self.handle, items_list, len(items_list))
        xbmcplugin.setContent(self.handle, content_type)
        xbmcplugin.endOfDirectory(self.handle)

    def play(self, album_id, track_id, **kwargs):
        track = Track(album_id, track_id)
        item = xbmcgui.ListItem(path=track.mp3)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def search(self, **kwargs):
        keyboard = xbmc.Keyboard()
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_response = self.api.search(keyboard.getText(), search_type='albums')
            album_list = get_album_list(search_response['albums']['items'])

            xbmcplugin.addDirectoryItems(self.handle, album_list, len(album_list))
            xbmcplugin.setContent(self.handle, 'albums')
            xbmcplugin.endOfDirectory(self.handle)

        else:
            self.main()

    def showMessage(self, msg):
        log(msg)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("Info", msg, str(5 * 1000)))

    def showErrorMessage(self, msg):
        log(msg)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))


def log(msg, level=xbmc.LOGNOTICE):
    log_message = u'{0}: {1}'.format('yandex.music', msg)
    xbmc.log(log_message.encode("utf-8"), level)


plugin = MusicYandex()
plugin.main()
# TODO: поиск с выбором того что ищеш, радио
