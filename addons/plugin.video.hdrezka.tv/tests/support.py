# tests/support.py
"""Shared harness: sys.path wiring, settings, fake transport, fixtures."""

import os
import sys
import tempfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.dirname(TESTS_DIR)
REPO_ROOT = os.path.dirname(os.path.dirname(ADDON_DIR))

sys.argv = ['plugin://plugin.video.hdrezka.tv/', '1', '']
sys.path.insert(0, os.path.join(TESTS_DIR, 'mock_kodi'))
sys.path.insert(0, ADDON_DIR)
sys.path.insert(0, os.path.join(ADDON_DIR, 'resources', 'lib'))
sys.path.insert(0, os.path.join(REPO_ROOT, 'addons', 'script.module.xbmc.helpers', 'lib'))
sys.path.insert(0, os.path.join(REPO_ROOT, 'addons', 'script.module.translit', 'lib'))
sys.path.insert(0, os.path.join(REPO_ROOT, 'addons', 'script.module.dandy.search.history', 'resources', 'lib'))

# NOTE: plain top-level imports on purpose: the addon does `import xbmc*`,
# so the mocks must live under those exact sys.modules keys. Importing
# them as `mock_kodi.x` would create shadow copies (settings/recorders
# would diverge between tests and the addon).
import xbmc  # noqa: E402
import xbmcaddon  # noqa: E402
import xbmcgui  # noqa: E402
import xbmcplugin  # noqa: E402
import xbmcvfs  # noqa: E402

ADDON_ID = 'plugin.video.hdrezka.tv'
xbmcaddon.ADDON_PATH = ADDON_DIR
xbmcaddon.PATHS.update({
    'script.module.translit': os.path.join(REPO_ROOT, 'addons', 'script.module.translit'),
    'script.module.dandy.search.history': os.path.join(REPO_ROOT, 'addons', 'script.module.dandy.search.history'),
    'script.module.xbmc.helpers': os.path.join(REPO_ROOT, 'addons', 'script.module.xbmc.helpers'),
})

import default  # noqa: E402
import helpers  # noqa: E402
import router  # noqa: E402
from cache import HDRezkaCache  # noqa: E402
from HDRezkaPlayer import HDRezkaPlayer  # noqa: E402

BASE_SETTINGS = {
    'use_transliteration': 'false',
    'quality': '720p',
    'translator': 'default',
    'dom_protocol': 'https',
    'domain': 'rezka.fi',
    'show_description': 'false',
    'use_atl_names': 'false',
    'use_proxy': 'false',
    'cookies': '',
}

BASE_STRINGS = {
    30000: 'Поиск',
    30003: 'Категории',
    30004: 'Следующая страница ...',
    30005: 'Сезон',
    30006: 'Выбрать озвучку',
    30008: 'История поиска',
    30009: 'Последние поступления',
    30010: 'Популярные',
    30011: 'В ожидании',
    30012: 'Сейчас смотрят',
    30013: 'Продолжить просмотр',
    30014: 'Перевод: %s',
    30015: 'Удалить из истории',
    30016: 'Удалить из Продолжить просмотр',
    30017: 'Успешно удалено из истории',
    30018: 'Успешно удалено из Продолжить просмотр',
    30019: 'Премиум',
}


def reset_all(overrides=None):
    xbmc.reset()
    xbmcaddon.reset()
    xbmcgui.reset()
    xbmcplugin.reset()
    xbmcaddon.PROFILE_DIR = tempfile.mkdtemp(prefix='hdrezka_test_')
    xbmcaddon.STRINGS.update(BASE_STRINGS)
    for key, value in BASE_SETTINGS.items():
        xbmcaddon.STORE[(ADDON_ID, key)] = value
    if overrides:
        for key, value in overrides.items():
            xbmcaddon.STORE[(ADDON_ID, key)] = value
    xbmcgui.Dialog.select_result = 0


class FakeResponse:
    def __init__(self, text='', json_data=None, json_exc=None, status_code=200):
        self.text = text
        self._json_data = json_data
        self._json_exc = json_exc
        self.status_code = status_code
        self.cookies = []

    def json(self):
        if self._json_exc is not None:
            raise self._json_exc
        return self._json_data


class FakeTransport:
    """Callable replacing HdrezkaTV.make_response. Routes: {(method, uri): response|[responses]}."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def _key(self, method, uri):
        base = uri.split('?')[0]
        candidates = [(method, uri), (method, base)]
        if '://' in base:
            candidates.append((method, '/' + base.split('://', 1)[1].split('/', 1)[1]))
        for key in candidates:
            if key in self.routes:
                return key
        raise AssertionError('unexpected request %r %r' % (method, uri))

    def __call__(self, method, uri, params=None, data=None, cookies=None, headers=None, **kwargs):
        self.calls.append({'method': method, 'uri': uri, 'params': params, 'data': data})
        key = self._key(method, uri)
        route = self.routes[key]
        if isinstance(route, list):
            if not route:
                raise AssertionError('route exhausted %r' % (key,))
            return route.pop(0)
        return route


def make_plugin(routes=None, settings=None):
    reset_all(settings)
    plugin = default.HdrezkaTV()
    plugin.make_response = FakeTransport(routes or {})
    return plugin


# Real translators-list markup (premium flags included).
TRANSLATORS_DIV = (
    '<li title="HDrezka Studio" class="b-translator__item b-prem_translator active" data-translator_id="111">HDrezka Studio</li>'
    '<li title="Дубляж" class="b-translator__item" data-translator_id="56">Дубляж</li>'
    '<li title="лостфильм (LostFilm)" class="b-translator__item" data-translator_id="1">лостфильм (LostFilm)</li>'
    '<li title="HDrezka Studio " class="b-translator__item b-prem_translator" data-translator_id="376">HDrezka Studio '
    '<img title="Украинский" src="https://statichdrezka.ac/i/flags/ua.png" height="16" width="16" alt="Украинский" /></li>'
)


def series_page(post_id='92422', translators=TRANSLATORS_DIV):
    return (
        '<div class="b-content__main">'
        '<img itemprop="image" src="https://statichdrezka.ac/i/x.jpg">'
        '<h1>Тестовый сериал</h1>'
        '<ul id="translators-list">' + translators + '</ul>'
        '</div>'
        '<input id="post_id" value="' + post_id + '">'
        '<div id="simple-episodes-tabs"></div>'
    )


EPISODES_JSON = {
    'episodes': (
        '<ul class="b-simple_episodes__list clearfix">'
        '<li data-id="11" data-season_id="1" data-episode_id="1">1 серия</li>'
        '<li data-id="12" data-season_id="1" data-episode_id="2">2 серия</li>'
        '<li data-id="23" data-season_id="2" data-episode_id="3">3 серия</li>'
        '</ul>'
    )
}

# Stream blocks as the site sends them (adjacent or separated - both parse).
STREAMS_BLOCK = '[720p]http://cdn/x720.mp4[1080p]http://cdn/x1080.mp4'

MOVIE_AJAX_OK = {'url': STREAMS_BLOCK, 'subtitle': 'ru]http://cdn/s.vtt'}

GET_STREAM_JSON = {'url': '[480p] http://cdn/e480.mp4, [720p] http://cdn/e720.mp4', 'subtitle': False}


def movie_page():
    return (
        '<div class="b-content__main">'
        '<img itemprop="image" src="https://statichdrezka.ac/i/y.jpg">'
        '<h1>Тестовый фильм</h1>'
        '<ul id="translators-list">' + TRANSLATORS_DIV + '</ul>'
        '</div>'
        '<input id="post_id" value="777">'
        '"streams":"' + STREAMS_BLOCK + '"'
    )


def index_page():
    return (
        '<div class="b-content__inline_items">'
        '<div class="b-content__inline_item" data-id="100">'
        '<div class="b-content__inline_item-link">'
        '<a href="https://rezka.fi/films/drama/100-test-2025.html">Тестовый фильм</a>'
        '<div>2025, Россия, Драмы</div>'
        '<!-- <div> <span class="b-content__inline_item-prem-label">Дубляж</span> </div> -->'
        '</div>'
        '<div class="b-content__inline_item-cover"><a href="x"><img src="/i/100.jpg"></a></div>'
        '</div>'
        '<div class="b-content__inline_item" data-id="200">'
        '<div class="b-content__inline_item-link">'
        '<a href="https://rezka.fi/series/drama/200-test-2025.html">Тестовый сериал</a>'
        '<div>2025, Россия, Драмы</div>'
        '<!-- <div> <span class="b-content__inline_item-prem-label">Дубляж</span> </div> -->'
        '</div>'
        '<div class="b-content__inline_item-cover"><a href="x"><img src="/i/200.jpg"></a>'
        '<span class="info">1 сезон</span></div>'
        '</div>'
        '</div>'
    )


def index_page_plain():
    # same template but without the commented prem-label divs (one div per item)
    return (
        '<div class="b-content__inline_items">'
        '<div class="b-content__inline_item" data-id="100">'
        '<div class="b-content__inline_item-link">'
        '<a href="https://rezka.fi/films/drama/100-test-2025.html">Тестовый фильм</a>'
        '<div>2025, Россия, Драмы</div>'
        '</div>'
        '<div class="b-content__inline_item-cover"><a href="x"><img src="/i/100.jpg"></a></div>'
        '</div>'
        '<div class="b-content__inline_item" data-id="200">'
        '<div class="b-content__inline_item-link">'
        '<a href="https://rezka.fi/series/drama/200-test-2025.html">Тестовый сериал</a>'
        '<div>2025, Россия, Драмы</div>'
        '</div>'
        '<div class="b-content__inline_item-cover"><a href="x"><img src="/i/200.jpg"></a>'
        '<span class="info">1 сезон</span></div>'
        '</div>'
        '</div>'
    )


BUBBLE_HTML = (
    '<div class="b-content__bubble_text">Описание фильма</div>'
    '<b style="color: #333;">16+</b>'
    '<div class="b-content__bubble_rating"><b>7.5</b></div>'
    '<span class="imdb"><b>7.1</b></span>'
    '<span class="kp"><b>6.9</b></span>'
)


def continue_page():
    return (
        '<div class="b-videosaves__list_item">'
        '<div class="td title"><a href="https://rezka.fi/series/drama/200-test-2025.html" data-cover_url="https://statichdrezka.ac/i/200.jpg">Тестовый сериал <small>(2025)</small></a></div>'
        '<div class="td info"><a href="https://rezka.fi/series/drama/200-test-2025.html">1 сезон 5 серия смотреть ещё 3</a></div>'
        '<div class="td controls"><a class="i-sprt delete" data-id="555"></a></div>'
        '</div>'
        '<div class="b-videosaves__list_item">'
        '<div class="td title"><a href="https://rezka.fi/films/drama/100-test-2025.html" data-cover_url="https://statichdrezka.ac/i/100.jpg">Тестовый фильм <small>(2025)</small></a></div>'
        '<div class="td info"><a href="https://rezka.fi/films/drama/100-test-2025.html">смотреть</a></div>'
        '<div class="td controls"><a class="i-sprt delete" data-id="556"></a></div>'
        '</div>'
    )


ANUBIS_HTML = (
    '<div id="anubis_challenge">'
    '{"challenge": {"id": "c1", "randomData": "abc", "difficulty": 0}}'
    '</div>'
)


class FakeSession:
    def __init__(self):
        self.posts = []

    def request(self, method, url, data=None, headers=None, **kwargs):
        self.posts.append({'method': method, 'url': url, 'data': data})
        return FakeResponse(text='{"success":true}', status_code=200)


class FakeHdrezkaTV:
    url = 'https://rezka.fi'
    domain = 'rezka.fi'

    def __init__(self, session=None):
        self.session = session or FakeSession()
        self.saved = 0

    def _save_session(self):
        self.saved += 1
