# -*- coding: utf-8 -*-
from abc import abstractmethod
from xml.etree import ElementTree
import http.cookiejar as cookielib

import requests


GENRES = {"all": "Музыка всех жанров",
        "pop": "Поп",
        "indie": "Инди",
        "rock": "Рок",
        "metal": "Метал",
        "alternative": "Альтернатива",
        "electronics": "Электроника",
        "electronic": "Электроника",
        "dance": "Танцевальная",
        "rap": "Рэп и хип-хоп",
        "hip-hop": "Рэп и хип-хоп",
        "rnb": "R&B",
        "r-n-b": "R&B",
        "jazz": "Джаз",
        "blues": "Блюз",
        "reggae": "Регги",
        "ska": "Ска",
        "punk": "Панк",
        "folk": "Музыка мира",
        "world": "Музыка мира",
        "classical": "Классика",
        "estrada": "Эстрада",
        "shanson": "Шансон",
        "country": "Кантри",
        "soundtrack": "Саундтреки",
        "relax": "Лёгкая музыка",
        "easy": "Лёгкая музыка",
        "bard": "Авторская песня",
        "singer-songwriter": "Авторская песня",
        "forchildren": "Детская",
        "for-children": "Детская",
        "fairytales": "Аудиосказки",
        "other": "Другое",
        "ruspop": "Русская поп-музыка",
        "disco": "Диско",
        "kpop": "K-pop",
        "local-indie": "Местное",
        "rusrock": "Русский рок",
        "rnr": "Рок-н-ролл",
        "rock-n-roll": "Рок-н-ролл",
        "prog": "Прогрессивный рок",
        "prog-rock": "Прогрессивный рок",
        "postrock": "Пост-рок",
        "post-rock": "Пост-рок",
        "newwave": "New Wave",
        "new-wave": "New Wave",
        "ukrrock": "Украинский рок",
        "folkrock": "Фолк-рок",
        "stonerrock": "Стоунер-рок",
        "hardrock": "Хард-рок",
        "classicmetal": "Классический метал",
        "progmetal": "Прогрессив метал",
        "numetal": "Ню-метал",
        "epicmetal": "Эпический метал",
        "folkmetal": "Фолк метал",
        "extrememetal": "Экстрим метал",
        "industrial": "Индастриал",
        "posthardcore": "Пост-хардкор",
        "hardcore": "Хардкор",
        "dubstep": "Дабстеп",
        "experimental": "Экспериментальная",
        "house": "Хаус",
        "techno": "Техно",
        "trance": "Транс",
        "dnb": "Драм-н-бэйс",
        "drum-n-bass": "Драм-н-бэйс",
        "rusrap": "Русский рэп",
        "foreignrap": "Иностранный рэп",
        "urban": "R&B и Урбан",
        "soul": "Соул",
        "funk": "Фанк",
        "tradjazz": "Традиционный",
        "trad-jass": "Традиционный",
        "conjazz": "Современный",
        "modern-jazz": "Современный",
        "reggaeton": "Реггетон",
        "dub": "Даб",
        "rusfolk": "Русская",
        "russian": "Русская",
        "tatar": "Татарская",
        "caucasian": "Кавказская",
        "celtic": "Кельтская",
        "balkan": "Балканская",
        "eurofolk": "Европейская",
        "european": "Европейская",
        "jewish": "Еврейская",
        "eastern": "Восточная",
        "african": "Африканская",
        "latinfolk": "Латиноамериканская",
        "latin-american": "Латиноамериканская",
        "amerfolk": "Американская",
        "american": "Американская",
        "romances": "Романсы",
        "argentinetango": "Аргентинское танго",
        "vocal": "Вокал",
        "opera": "Вокал",
        "modern": "Современная классика",
        "modern-classical": "Современная классика",
        "rusestrada": "Русская",
        "films": "Из фильмов",
        "tvseries": "Из сериалов",
        "tv-series": "Из сериалов",
        "animated": "Из мультфильмов",
        "animated-films": "Из мультфильмов",
        "videogame": "Из видеоигр",
        "videogame-music": "Из видеоигр",
        "musical": "Мюзиклы",
        "bollywood": "Болливуд",
        "lounge": "Лаундж",
        "newage": "Нью-эйдж",
        "new-age": "Нью-эйдж",
        "meditation": "Медитация",
        "meditative": "Медитация",
        "rusbards": "Русская",
        "foreignbard": "Иностранная",
        "sport": "Спортивная",
        "holiday": "Праздничная",
        "spoken": "Аудиокниги",
        "audio-books": "Аудиокниги",
        "children": "Детская",
        "news": "Новости",
        "society": "Общество и культура",
        "education": "Образование",
        }


def get_image(image):
    if not image:
        return 'https://music.yandex.ru/blocks/common/default.200x200.png'
    return 'https://' + image.replace('%%', 'orig')


def get_artists(obj):
    return ', '.join(artist['name'] for artist in obj['artists'])


def get_labels(obj):
    return ', '.join(label['name'] for label in obj['labels'])


def get_genre(obj, multiply=False):
    if multiply:
        genres_list = []
        for genre in obj:
            genres_list.append(GENRES.get(genre, genre))
        return ', '.join(genres_list)
    genre = obj.get('genre')
    return GENRES.get(genre, genre)


def get_duration(obj):
    return obj.get('durationMs', 0) / 1000


class AbstractYandexModel(object):
    url = 'https://music.yandex.ru'
    default_params = {'lang': 'ru'}
    default_headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0", "Referer" : url}
    session = None

    def __init__(self):
        self.body = self.connect()
        AbstractYandexModel.session = AbstractYandexModel.session or requests.Session()

    @abstractmethod
    def connect(self):
        pass

    @staticmethod
    def auth(login, password, cookie_jar, forced=False):
        AbstractYandexModel.session = AbstractYandexModel.session or requests.Session()
        AbstractYandexModel.session.cookies = cookielib.LWPCookieJar(cookie_jar)

        need_auth = False

        try:
            AbstractYandexModel.session.cookies.load()
        except:
            need_auth = True
            
        if need_auth or forced:            
            data = 'login={0}&password={1}&twoweeks=yes&retpath=https://music.yandex.ru/blocks/auth/login-status.html'.format(login, password)
            AbstractYandexModel.session.post('https://passport.yandex.ru/passport?mode=embeddedauth&retpath=https%3A%2F%2Fmusic.yandex.ru%2F', data=data)
            AbstractYandexModel.session.cookies.save()

        cookies = requests.utils.dict_from_cookiejar(AbstractYandexModel.session.cookies)

        return cookies.get('yandex_login') != None

    def make_response(self, url, params=None, data=None, cookies=None, headers={}):
        if params:
            params.update(**self.default_params)

        headers.update(**self.default_headers)

        return AbstractYandexModel.session.get(self.url + url, params=params, data=data, cookies=cookies, headers=headers).json()

    def __getattr__(self, item):
        return self.body.get(item)


class Album(AbstractYandexModel):
    def __init__(self, id):
        self.id = id
        super(Album, self).__init__()

    @property
    def image(self):
        return get_image(self.body['coverUri'])

    @property
    def artist(self):
        return get_artists(self.body)

    @property
    def genre(self):
        return get_genre(self.body)

    def connect(self):
        params = {
            'album': self.id,
        }
        return self.make_response('/handlers/album.jsx', params=params)


class Playlist(AbstractYandexModel):
    def __init__(self, owner_id, id):
        self.owner_id = owner_id
        self.id = id
        super(Playlist, self).__init__()

    @property
    def image(self):
        return get_image(self.body['playlist']['cover']['uri'])

    def connect(self):
        params = {
            'owner': self.owner_id,
            'kinds': self.id
        }
        return self.make_response('/handlers/playlist.jsx', params=params)


class Track(AbstractYandexModel):
    def __init__(self, album_id, id, own=False):
        self.album_id = album_id
        self.id = id
        self.own = own
        super(Track, self).__init__()

    def connect(self):
        headers = {
            'X-Retpath-Y': '%s/album/%s' % (self.url, self.album_id),
        }
        if self.own:
            url = '/api/v2.1/handlers/track/%s/web-own_playlists-playlist-track-saved/download/m?hq=1' % (self.id)
        else:
            url = '/api/v2.1/handlers/track/%s:%s/web-album-track-track-main/download/m?hq=1' % (self.id, self.album_id)
        return self.make_response(url, headers=headers)

    @property
    def mp3(self):
        uri = self.body['src']
        uri = 'https:' + uri if uri[:2] == '//' else uri

        response = requests.get(uri)

        tree = ElementTree.fromstring(response.content)
        return 'http://%s/get-mp3/%s/%s%s?track-id=%s&region=225&from=service-search' % (
            tree.find('.host').text,
            tree.find('.s').text,
            tree.find('.ts').text,
            tree.find('.path').text,
            self.id,
        )


class Artist(AbstractYandexModel):
    def __init__(self, artist_id):
        self.artist_id = artist_id
        super(Artist, self).__init__()

    def connect(self):
        params = {
            'artist': self.artist_id,
            'what': 'albums'
        }
        return self.make_response('/handlers/artist.jsx', params=params)


class YandexMusic(AbstractYandexModel):
    def connect(self):
        pass

    def main(self, what, **kwargs):
        params = {
            'what': what
        }
        params.update(kwargs)

        return self.make_response('/handlers/main.jsx', params=params)

    def get_albums(self, ids):
        params = {
            'albumIds': ','.join(map(str, ids))
        }
        return self.make_response('/handlers/albums.jsx', params=params)

    def get_playlists(self, ids):
        data = {
            'ids': ','.join(map(str, ids))
        }
        return self.make_response('/handlers/playlists-enchanced.jsx', data=data)

    def search(self, text, search_type='all'):
        params = {
            'text': text,
            'type': search_type
        }
        return self.make_response('/handlers/music-search.jsx', params=params)

    def library(self, owner, filter_name):
        params = {
            'owner': owner,
            'filter': filter_name,
            'likeFilter': 'favorite',
        }
        return self.make_response('/handlers/library.jsx', params=params)

    def feeds(self, owner):
        cookies = {
            'yandex_login': owner,
        }
        return self.make_response('/handlers/feed.jsx', cookies=cookies)
