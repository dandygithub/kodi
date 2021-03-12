# -*- coding: utf-8 -*-

import sys, os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from api import YandexMusic, Album, Playlist, Track, Artist, get_image, get_artists, get_genre, get_duration, get_labels


__all__ = ['run']

class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        result = instance.__dict__[self.func.__name__] = self.func(instance)
        return result


def get_track_list(album_id, tracks, info=None):
    track_list = []
    for number, track in enumerate(tracks, start=1):
        if track.get('error'):
            continue

        artists = get_artists(track)

        if artists:
            name = "[COLOR=FF00FFF0]%s[/COLOR] - %s" % (artists, track['title'])
        else:
            name = track['title']

        if not track['available']:
            name = '[COLOR=red][B]$[/B][/COLOR] ' + name

        li = xbmcgui.ListItem(name)

        image = track.get('ogImage') or track.get('coverUri', '')
        image = get_image(image)
        li.setArt({'thumb': image})

        if album_id is None:
            albums = track.get('albums')
            if albums:
                album_id = albums[0]['id']
                info = {'year': albums[0].get('year'), 'genre': get_genre(albums[0])}

        info_labels = {
            'mediatype': 'song',
            'tracknumber': number,
            'artist': artists,
            'size': track.get('fileSize', 0),
            'duration': get_duration(track),
            'title': track['title'],
            'genre': get_genre(track)
        }
        if info:
            info_labels.update(**info)

        li.setInfo(type='music', infoLabels=info_labels)
        li.setProperty('IsPlayable', 'true')

        own = 'true' if track.get('storageDir') else 'false'

        url = sys.argv[0] + '?mode=%s&album_id=%s&track_id=%s&own=%s' % ('play', album_id, track['id'], own)
        track_list.append((url, li, False))
    return track_list


def get_album_list(albums):
    album_list = []
    for album in albums:
        if album.get('error'):
            continue

        artists = get_artists(album)

        if artists:
            name = "[COLOR=FF00FFF0]%s[/COLOR] - %s" % (artists, album['title'])
        else:
            name = album['title']

        li = xbmcgui.ListItem(name)
        li.setArt({'thumb': get_image(album.get('coverUri'))})

        li.setInfo(
            type='music',
            infoLabels={
                'genre': get_genre(album)
            }
        )

        url = sys.argv[0] + '?mode=%s&album_id=%s' % ('show_album', album['id'])
        album_list.append((url, li, True))
    return album_list


def get_playlist_list(playlists):
    playlist_list = []
    for playlist in playlists:
        if playlist.get('error'):
            continue

        li = xbmcgui.ListItem(
            "[COLOR=FF00FFF0]%s[/COLOR] - %s" % (playlist['owner']['name'], playlist['title']))

        if playlist['kind'] == 3:
            playlist['uid'] = playlist['owner']['uid']
            li.setArt({'thumb': 'https://music.yandex.ru/blocks/playlist-cover/playlist-cover_like.png'})
        else:
            li.setArt({'thumb': get_image(playlist['ogImage'])})

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


def get_podcast_list(podcasts):
    podcast_list = []
    for podcast in podcasts:
        if podcast.get('error'):
            continue

        labels = get_labels(podcast)
        if labels:
            title = "[COLOR=FF00FFF0]%s[/COLOR] - %s" % (labels, podcast['title'])
        else:
            title = podcast['title']

        li = xbmcgui.ListItem(title)
        li.setArt({'thumb': get_image(podcast.get('coverUri'))})

        li.setInfo(
            type='music',
            infoLabels={
                'genre': get_genre(podcast)
            }
        )

        url = sys.argv[0] + '?mode=%s&album_id=%s' % ('show_album', podcast['id'])
        podcast_list.append((url, li, True))
    return podcast_list


def get_artist_list(artists):
    playlist_list = []
    for artist in artists:
        if artist.get('error'):
            continue

        name = artist.get('name', '[COLOR=red]No name[/COLOR]')

        li = xbmcgui.ListItem("[COLOR=FF00FFF0]%s[/COLOR]" % name)
        li.setArt({'thumb': get_image(artist['ogImage'])})

        rating = artist.get('ratings').get('month')

        li.setInfo(
            type='music',
            infoLabels={
                'title': name,
                'genre': get_genre(artist['genres'], multiply=True),
                'rating': rating
            }
        )

        url = sys.argv[0] + '?mode=%s&artist_id=%s' % ('show_artist', artist['id'])
        playlist_list.append((url, li, True))
    return playlist_list


class MusicYandex:
    def __init__(self):
        self.id = 'plugin.audio.music.yandex'
        self.settings = self._load_settings()

        if self.settings['account']:
            self.auth()

        self.api = YandexMusic()
        self.language = self.addon.getLocalizedString
        self.handle = int(sys.argv[1])
        self.patterns = self._load_patterns()

    @cached_property
    def addon(self):
        return xbmcaddon.Addon(self.id)

    def _load_settings(self):
        login = self.addon.getSetting('login')
        password = self.addon.getSetting('password')
        if not login:
            account = False
        else:
            account = {'owner':login.split('@')[0], 'login':login, 'password':password, 'authorized':False}

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
            'auth': self.auth,
        }
        return patterns

    def main(self):
        params = get_parameters(sys.argv[2])
        method = self.patterns.get(params.get('mode'))
        if not method:
            return self.menu()
        return method(**params)

    def draw_menu(self, routers):
        for router in routers:
            url = sys.argv[0] + router['uri']

            item = xbmcgui.ListItem(router['name'])
            item.setArt({'thumb': self.settings['icon']})

            item.setProperty('fanart_image', self.settings['fanart'])
            xbmcplugin.addDirectoryItem(self.handle, url, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def menu(self):
        routers = [
            {'name': '[COLOR=FF00FF00][Поиск][/COLOR]', 'uri': '?mode=search'},
            {'name': '[COLOR=FF00FFFF]Новые плейлисты[/COLOR]', 'uri': '?mode=index&what=new-playlists'},
            {'name': '[COLOR=FF00FFFF]Новые релизы[/COLOR]', 'uri': '?mode=index&what=new-releases'},
            {'name': '[COLOR=FF00FFFF]Чарт[/COLOR]', 'uri': '?mode=index&what=chart&chartType=tracks'}
        ]
        if self.settings['account'] and self.settings['account']['authorized']:
            routers.extend([
                {'name': '[COLOR=FF00FF00]Моя музыка[/COLOR]', 'uri': '?mode=my'},
            ])
        else:
            routers.extend([
                {'name': '[B]Войти[/B]', 'uri': '?mode=auth&forced=true'},
            ])

        return self.draw_menu(routers)

    def show_playlist(self, owner_id, playlist_id, **kwargs):
        playlist = Playlist(owner_id, playlist_id)

        track_list = []

        if playlist.playlist.get('tracks'):
            track_list = get_track_list(album_id=playlist.id, tracks=playlist.playlist['tracks'])

        xbmcplugin.addDirectoryItems(self.handle, track_list, len(track_list))
        xbmcplugin.setContent(self.handle, 'albums')
        xbmcplugin.endOfDirectory(self.handle)

    def show_album(self, album_id, **kwargs):
        album = Album(album_id)
        info = {'year': album.year, 'genre': album.genre}
        track_list = get_track_list(album_id=album_id, tracks=album.volumes[0], info=info)

        xbmcplugin.addDirectoryItems(self.handle, track_list, len(track_list))
        xbmcplugin.setContent(self.handle, 'albums')
        xbmcplugin.endOfDirectory(self.handle)

    def show_artist(self, artist_id, **kwargs):
        artist = Artist(artist_id)
        album_list = get_album_list(artist.albums)

        xbmcplugin.addDirectoryItems(self.handle, album_list, len(album_list))
        xbmcplugin.setContent(self.handle, 'albums')
        xbmcplugin.endOfDirectory(self.handle)

    def index(self, what, **kwargs):
        kwargs.pop('mode')

        response = self.api.main(what, **kwargs)

        if what == 'new-playlists':
            ids = ('%s:%s' % (playlist['uid'], playlist['kind']) for playlist in response['newPlaylists'])
            items = get_playlist_list(self.api.get_playlists(ids))
        elif what == 'new-releases':
            items = get_album_list(self.api.get_albums(response['newReleases']))
        elif what == 'chart':
            items = get_track_list(None, response['chart']['tracks'])
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
                {'name': '[COLOR=FF00FFFF]Подкасты[/COLOR]', 'uri': '?mode=my&filter_name=podcasts'},
                {'name': '[COLOR=FF00FFFF]Исполнители[/COLOR]', 'uri': '?mode=my&filter_name=artists'},
            ]
            return self.draw_menu(routers)

        library = self.api.library(self.settings['account']['owner'], filter_name)

        if filter_name == 'tracks':
            items_list = get_track_list(album_id=library['owner']['uid'], tracks=library['tracks'])
            content_type = 'albums'
        elif filter_name == 'albums':
            items_list = get_album_list(library['albums'])
            content_type = 'albums'
        elif filter_name == 'playlists':
            items_list = get_playlist_list(library['bookmarks'])
            items_list = items_list + get_playlist_list(library['playlists'])
            content_type = 'albums'
        elif filter_name == 'artists':
            items_list = get_artist_list(library['artists'])
            content_type = 'artists'
        elif filter_name == 'podcasts':
            items_list = get_podcast_list(library['albums'])
            content_type = 'albums'
        else:
            items_list = []
            content_type = ''

        xbmcplugin.addDirectoryItems(self.handle, items_list, len(items_list))
        xbmcplugin.setContent(self.handle, content_type)
        xbmcplugin.endOfDirectory(self.handle)

    def play(self, album_id, track_id, own, **kwargs):
        track = Track(album_id, track_id, own == 'true')
        item = xbmcgui.ListItem(path=track.mp3)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def search(self, **kwargs):
        keyboard = xbmc.Keyboard()
        keyboard.doModal()
        if keyboard.isConfirmed():
            keywords = keyboard.getText()
            if keywords:
                search_response = self.api.search(keywords, search_type='albums')

                album_list = get_album_list(search_response['albums']['items'])

                xbmcplugin.addDirectoryItems(self.handle, album_list, len(album_list))
                xbmcplugin.setContent(self.handle, 'albums')
                xbmcplugin.endOfDirectory(self.handle)

        return

    def auth(self, forced=None, **kwargs):
        forced = forced == 'true'
        if self.settings['account']:
            fcookies = os.path.join(self.addon.getAddonInfo('path'), 'cookies.txt')
            self.settings['account']['authorized'] = YandexMusic.auth(self.settings['account']['login'], self.settings['account']['password'], fcookies, forced)
        if forced:
            if not self.settings['account']:
                self.addon.openSettings()
            else:
                xbmc.executebuiltin('Container.Refresh')

    def showMessage(self, msg):
        log(msg)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("Info", msg, str(5 * 1000)))

    def showErrorMessage(self, msg):
        log(msg)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))


def log(msg, level=xbmc.LOGWARNING):
    log_message = u'{0}: {1}'.format('yandex.music', msg)
    xbmc.log(log_message.encode("utf-8"), level)

def get_parameters(source):
    params = {}
    if not source:
        return params
    source = source.replace('?', '')
    for item in source.split('&'):
        key, value = item.split('=', 1)
        params[key] = value
    return params

def run():
    plugin = MusicYandex()
    plugin.main()
