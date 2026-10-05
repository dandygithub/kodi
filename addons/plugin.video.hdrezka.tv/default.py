#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Writer (c) 2012-2025, MrStealth, dandy

import os
import re
import sys
import socket
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
import XbmcHelpers
import SearchHistory as history
from Translit import Translit

import requests

import actions
import helpers
import router
from voidboost import parse_streams

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import json
import urllib.parse
import time

import hashlib
import sys

ADDON_PATH = os.path.dirname(__file__)
LIB_PATH = os.path.join(ADDON_PATH, "resources", "lib")

if LIB_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)
xbmc.log(str(sys.path), xbmc.LOGINFO)
from cache import HDRezkaCache

if LIB_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)


def anubis_pow(random_data, difficulty):

    nonce = 0

    zero_bytes = difficulty // 2
    half = difficulty % 2

    while True:

        digest = hashlib.sha256(
            (random_data + str(nonce)).encode()
        ).digest()

        ok = True

        for i in range(zero_bytes):
            if digest[i] != 0:
                ok = False
                break

        if ok and half:
            if digest[zero_bytes] >> 4 != 0:
                ok = False

        if ok:
            return digest.hex(), nonce

        nonce += 1


retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500,502,503,504]
)


common = XbmcHelpers
transliterate = Translit()

socket.setdefaulttimeout(120)

USER_AGENT = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0"

CDN_SERIES_URL = "/ajax/get_cdn_series/"
RUN_PLUGIN_FMT = "RunPlugin(%s)"
CONTAINER_REFRESH = "Container.Refresh()"
BUBBLE_CACHE_TTL = 3 * 24 * 3600

ANUBIS_CHALLENGE_RE = re.compile(
    r'<([a-z][a-z0-9]*)[^>]*\bid\s*=\s*["\']anubis_challenge["\'][^>]*>(.{0,10000}?)</\1\s*>',
    re.S | re.I
)


class HdrezkaTV:

    def solve_anubis(self, html, url):

        m = ANUBIS_CHALLENGE_RE.search(html)

        if not m:
            helpers.log("No anubis_challenge found")
            return False

        data = json.loads(m.group(2))

        challenge = data["challenge"]

        start = time.time()

        hash_value, nonce = anubis_pow(
            challenge["randomData"],
            challenge["difficulty"]
        )

        elapsed = int((time.time()-start)*1000)


        helpers.log(
            f"Anubis solved nonce={nonce}"
        )


        from urllib.parse import urljoin

        pass_url = urljoin(
            self.url,
            "/.within.website/x/cmd/anubis/api/pass-challenge"
        )

        pass_url += "?" + urllib.parse.urlencode({
            "id": challenge["id"],
            "response": hash_value,
            "nonce": nonce,
            "elapsedTime": elapsed,
            "redir": url
        })


        r = self.make_response(
            'GET',
            pass_url,
            allow_redirects=False
        )


        helpers.log(
            f"Anubis pass status {r.status_code}"
        )

        helpers.log(
            f"Cookies: {self.session.cookies}"
        )

        return True

    def __init__(self):
        self.id = 'plugin.video.hdrezka.tv'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.icon_next = os.path.join(self.addon.getAddonInfo('path'), 'resources/icons/next.png')
        self.language = self.addon.getLocalizedString
        # service and RunScript invocations may come without a handle argument
        self.handle = int(sys.argv[1]) if len(sys.argv) > 1 else None
        self.profile = xbmcvfs.translatePath(self.addon.getAddonInfo('profile'))
        self.use_transliteration = self.addon.getSettingBool('use_transliteration')
        self.quality = self.addon.getSetting('quality')
        self.translator = self.addon.getSetting('translator')
        self.domain = self.addon.getSetting('domain')
        self.show_description = self.addon.getSettingBool('show_description')
        self.use_atl_names = self.addon.getSettingBool('use_atl_names')

        self.url = self.addon.getSetting('dom_protocol') + '://' + self.domain
        self.proxies = self._load_proxy_settings()
        self.session = self._load_session()

    def _save_session(self):
        try:
            self.addon.setSetting("cookies",helpers.dump_cookies(self.session.cookies))
        except Exception as e:
            helpers.log("save cookies failed: %s" % e)

    def _load_session(self):
        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            "User-Agent": USER_AGENT,
            "Referer": self.url + "/",
        })

        saved_cookies = self.addon.getSetting('cookies')
        if saved_cookies:
            session.cookies = helpers.load_cookies(
                self.addon.getSetting('cookies')
            )

        return session

    def _load_proxy_settings(self):
        if self.addon.getSetting('use_proxy') == 'false':
            return False
        proxy_protocol = self.addon.getSetting('protocol')
        proxy_url = self.addon.getSetting('proxy_url')
        return {
            'http': proxy_protocol + '://' + proxy_url,
            'https': proxy_protocol + '://' + proxy_url
        }

    def is_atl_mode(self, params=None):
        if params and params.get('atl', '').lower() == 'true':
            return True
        return self.use_atl_names

    def make_response(self, method, uri, params=None, data=None,cookies=None, headers=None, **kwargs):

        if cookies:
            self.session.cookies.update(cookies)

        try:
            response = self.session.request(
                method,
                self.url + uri,
                params=params,
                data=data,
                headers=headers,
                proxies=self.proxies,
                timeout=120,
                **kwargs
            )
        except requests.exceptions.RequestException as ex:
            # single retry with a pause: covers drops, resets and broken
            # chunks on any request kind (reads and idempotent-enough writes)
            helpers.log('make_response retry after ex: %s' % ex)
            time.sleep(2)
            response = self.session.request(
                method,
                self.url + uri,
                params=params,
                data=data,
                headers=headers,
                proxies=self.proxies,
                timeout=120,
                **kwargs
            )

        if cookies or response.cookies:
            self._save_session()

        return response

    def main(self, action):
        params = router.parse_uri(action)
        helpers.log(f'*** main params: {params}')

        mode = params.get('mode')
        if mode == 'play':
            self.play(params.get('url'))
        elif mode == 'play_episode':
            self.play_episode(
                params.get('url'),
                params.get('post_id'),
                params.get('season_id'),
                params.get('episode_id'),
                urllib.parse.unquote_plus(params.get('title') or ''),
                params.get('image'),
                params.get('idt'),
                params.get('strm'),
                params.get('show_id')
            )
        elif mode == 'select_translator':
            self.select_translator_item(
                params.get('uri'), params.get('via'), params.get('atl'), params.get('strm'))
        elif mode == 'show':
            self.show(params.get('uri'), self.is_atl_mode(params), params.get('strm'))
        elif mode == 'index':
            self.index(params.get('uri'), params.get('page'), params.get('query_filter'))
        elif mode == 'categories':
            self.categories()
        elif mode == 'sub_categories':
            self.sub_categories(params.get('uri'))
        elif mode == 'search':
            external = 'main' if 'main' in params else None
            if not external:
                external = 'usearch' if 'usearch' in params else None
            self.search(params.get('keyword'), external)
        elif mode == 'history':
            self.history()
        elif mode == 'history_delete':
            self.delete_history(params.get('keyword'))
        elif mode == 'continue':
            self.continues()
        elif mode == 'continue_delete':
            self.delete_continue(params.get('id'))
        elif mode == 'collections':
            self.collections(int(params.get('page', 1)))
        else:
            self.menu()

    def menu(self):
        menu_items = (
            ('search', 'FF00FF00', 30000),
            ('history', 'FF00FF00', 30008),
            ('categories', 'FF00FF00', 30003),
            ('index', 'FFDDD2CC', 30009),
            ('index_popular', 'FFDDD2CC', 30010),
            ('index_soon', 'FFDDD2CC', 30011),
            ('index_watching', 'FFDDD2CC', 30012),
            ('continue', 'FFDDD2CC', 30013),
        )
        for mode, color, translation_id in menu_items:
            uri = router.build_uri(mode)
            if '_' in mode:
                mode, query_filter = mode.split('_')
                uri = router.build_uri(mode, query_filter=query_filter)
            item = xbmcgui.ListItem(f'[COLOR={color}]{self.language(translation_id)}[/COLOR]')
            item.setArt({'thumb': self.icon})
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def categories(self):
        response = self.make_response('GET', '/')
        genres = common.parseDOM(response.text, "ul", attrs={"id": "topnav-menu"})

        titles = common.parseDOM(genres, "a", attrs={"class": "b-topnav__item-link"})
        links = common.parseDOM(genres, "a", attrs={"class": "b-topnav__item-link"}, ret='href')
        for i, title in enumerate(titles):
            title = common.stripTags(title)
            item_uri = router.build_uri('sub_categories', uri=links[i])
            item = xbmcgui.ListItem(title)
            item.setArt({'thumb': self.icon})
            xbmcplugin.addDirectoryItem(self.handle, item_uri, item, True)

        item_uri = router.build_uri('collections')
        item = xbmcgui.ListItem('Подборки')
        item.setArt({'thumb': self.icon})
        xbmcplugin.addDirectoryItem(self.handle, item_uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def sub_categories(self, uri):
        response = self.make_response('GET', '/')
        genres = common.parseDOM(response.text, "ul", attrs={"class": "left"})

        titles = common.parseDOM(genres, "a")
        links = common.parseDOM(genres, "a", ret='href')

        item_uri = router.build_uri('index', uri=uri)
        item = xbmcgui.ListItem(f'[COLOR=FF00FFF0]{self.language(30007)}[/COLOR]')
        item.setArt({'thumb': self.icon})
        xbmcplugin.addDirectoryItem(self.handle, item_uri, item, True)

        for i, title in enumerate(titles):
            if not links[i].startswith(uri):
                continue
            item_uri = router.build_uri('index', uri=links[i])
            item = xbmcgui.ListItem(title)
            item.setArt({'thumb': self.icon})
            xbmcplugin.addDirectoryItem(self.handle, item_uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def collections(self, page):
        uri = '/collections/'
        if page != 1:
            uri = f'/collections/page/{page}/'

        response = self.make_response('GET', uri)
        content = common.parseDOM(response.text, 'div', attrs={'class': 'b-content__collections_list clearfix'})
        titles = common.parseDOM(content, "a", attrs={"class": "title"})
        counts = common.parseDOM(content, 'div', attrs={"class": ".num"})
        links = common.parseDOM(content, "div", attrs={"class": "b-content__collections_item"}, ret="data-url")
        icons = common.parseDOM(content, "img", attrs={"class": "cover"}, ret="src")

        for i, name in enumerate(titles):
            item_uri = router.build_uri('index', uri=router.normalize_uri(links[i]))
            item = xbmcgui.ListItem(f'{name} [COLOR=55FFFFFF]({counts[i]})[/COLOR]')
            item.setArt({'thumb': icons[i]})
            xbmcplugin.addDirectoryItem(self.handle, item_uri, item, True)

        if not len(titles) < 32:
            item_uri = router.build_uri('collections', page=page + 1)
            item = xbmcgui.ListItem("[COLOR=orange]" + self.language(30004) + "[/COLOR]")
            item.setArt({'icon': self.icon_next})
            xbmcplugin.addDirectoryItem(self.handle, item_uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def index(self, uri=None, page=None, query_filter=None):
        url = uri
        if not url:
            url = '/'
        if page:
            url += f'page/{page}/'
        if query_filter:
            url += f'?filter={query_filter}'

        response = self.make_response('GET', url)
        content = common.parseDOM(response.text, "div", attrs={"class": "b-content__inline_items"})

        items = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"})
        post_ids = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"}, ret="data-id")

        link_containers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-link"})

        links = common.parseDOM(link_containers, "a", ret='href')
        titles = common.parseDOM(link_containers, "a")
        div_covers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-cover"})

        for i, name in enumerate(titles):
            info = self.get_item_additional_info(post_ids[i])
            country_divs = common.parseDOM(link_containers[i], "div")
            country_text = country_divs[0] if country_divs else ''
            title = helpers.built_title(name, country_text, **info)
            image = self._normalize_url(common.parseDOM(div_covers[i], "img", ret='src')[0])
            item_uri = router.build_uri('show', uri=router.normalize_uri(links[i]))
            year, country, genre = helpers.get_media_attributes(country_text)
            is_serial = common.parseDOM(div_covers[i], 'span', attrs={"class": "info"})
            item = xbmcgui.ListItem(title)
            item.setArt({'thumb': image, 'icon': image})
            item.addContextMenuItems(self._translator_menu(router.normalize_uri(links[i])))
            info_labels = {
                'title': title,
                'genre': genre,
                'country': country,
                'plot': info['description'],
                'rating': info['rating']['site']
            }
            if year:
                info_labels['year'] = year
            if info['age_limit']:
                info_labels['mpaa'] = info['age_limit']
            item.setInfo(type='video', infoLabels=info_labels)
            is_folder = True
            if (self.quality != 'select') and not is_serial:
                item.setProperty('IsPlayable', 'true')
                is_folder = False
            xbmcplugin.addDirectoryItem(self.handle, item_uri, item, is_folder)

        if not len(titles) < 16:
            params = {'page': 2, 'uri': uri}
            if page:
                params['page'] = int(page) + 1
            if query_filter:
                params['query_filter'] = query_filter
            item_uri = router.build_uri('index', **params)
            item = xbmcgui.ListItem("[COLOR=orange]" + self.language(30004) + "[/COLOR]")
            item.setArt({'icon': self.icon_next})
            xbmcplugin.addDirectoryItem(self.handle, item_uri, item, True)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def select_quality(self, streams, title, image, subtitles=None, strm=None, play_info=None):
        if strm == '1' and self.quality == 'select' and streams:
            name, quality, url = max(streams, key=lambda s: s[1])
            helpers.log(f'strm selected best quality name: {name}')
            self.play(url, subtitles, play_info, title)
            return
        for name, quality, url in streams:
            if self.quality != 'select' or strm == '1':
                if (name == self.quality) or (int(self.quality.split('p')[0]) >= quality):
                    helpers.log(f'selected quality name: {name}')
                    self.play(url, subtitles, play_info, title)
                    break
            else:
                film_title = f"{title} - [COLOR=orange]{name}[/COLOR]"
                item_uri = router.build_uri('play', url=url)
                item = xbmcgui.ListItem(film_title)
                item.setArt({'icon': image})
                item.setInfo(
                    type='Video',
                    infoLabels={'title': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0}
                )
                item.setProperty('IsPlayable', 'true')
                helpers.set_item_subtitles(item, subtitles)
                xbmcplugin.addDirectoryItem(self.handle, item_uri, item, False)

    def _parse_translators(self, content):
        try:
            div = common.parseDOM(content, 'ul', attrs={'id': 'translators-list'})[0]
        except Exception as ex:
            helpers.log(
                'parse translators fault ex: %s has_list=%s translator_id_count=%d'
                % (ex, 'translators-list' in content, content.count('data-translator_id'))
            )
            return None, None, None, None, None
        titles = common.parseDOM(div, 'li', ret='title')
        ids = common.parseDOM(div, 'li', ret="data-translator_id")

        # transform flag image into title suffix
        title_items = common.parseDOM(div, 'li')
        for index, title in enumerate(title_items):
            if index >= len(titles):
                break
            images = common.parseDOM(title, 'img', ret='title')
            for img in images:
                titles[index] += f' ({img})'

        directors = common.parseDOM(div, 'li', ret='data-director')
        li_tags = re.findall(r'<li\b[^>]*>', div)
        if len(li_tags) != len(titles):
            premium = [False] * len(titles)
        else:
            premium = ['b-prem_translator' in tag for tag in li_tags]
        active_id = None
        for index, tag in enumerate(li_tags):
            if index >= len(ids):
                break
            class_match = re.search(r'class\s*=\s*["\']([^"\']*)["\']', tag)
            if class_match and 'active' in class_match.group(1).split():
                active_id = ids[index]
                break
        return titles, ids, directors, premium, active_id

    def _get_cached_translator(self, post_id, ids):
        try:
            cached = HDRezkaCache(self.profile).get_post_translation(post_id)
        except Exception as ex:
            helpers.log(f'get cached translator fault ex: {ex}')
            return None
        if cached is not None and cached in (ids or []):
            return cached
        return None

    def _translator_menu(self, uri):
        item_uri = router.build_uri('select_translator', uri=uri, via='menu')
        return [(self.language(30006), RUN_PLUGIN_FMT % item_uri)]

    def _add_translator_item(self, titles, ids, premium, post_id, idt, uri):
        if not titles or not ids:
            return
        cached = self._get_cached_translator(post_id, ids)
        current = cached if cached is not None else idt
        try:
            current_index = ids.index(current)
            translator_name = titles[current_index]
        except Exception:
            current_index = 0
            translator_name = titles[0]
        try:
            stored_name = HDRezkaCache(self.profile).get_post_translation_name(post_id)
        except Exception:
            stored_name = None
        if stored_name:
            translator_name = stored_name
        if premium and current_index < len(premium) and premium[current_index]:
            translator_name = '%s [%s]' % (translator_name, self.language(30019))
        try:
            label = self.language(30014) % translator_name
        except Exception:
            label = translator_name
        item_uri = router.build_uri('select_translator', uri=uri, via='line')
        item = xbmcgui.ListItem(f'[COLOR=yellowgreen]{label}[/COLOR]')
        item.setArt({'thumb': self.icon, 'icon': self.icon})
        # explicit false: JSONRPC exposes requested ListItem properties to scans
        item.setProperty('IsPlayable', 'false')
        # Folder row served inline: scans skip folders, clicks never go empty.
        xbmcplugin.addDirectoryItem(self.handle, item_uri, item, True)

    def _cdn_headers(self, url):
        return {
            "Host": self.domain,
            "Origin": self.url,
            "Referer": url,
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest"
        }

    def _count_translator_episodes(self, post_id, translator_id, url, director=None):
        data = {
            "id": post_id,
            "translator_id": translator_id,
            "action": "get_episodes"
        }
        if director:
            data['is_director'] = director
        try:
            response = self.make_response('POST', CDN_SERIES_URL, data=data, headers=self._cdn_headers(url)).json()
            playlist = common.parseDOM(response["episodes"], "ul", attrs={"class": "b-simple_episodes__list clearfix"})
            return sum(len(common.parseDOM(block, "li")) for block in playlist)
        except Exception as ex:
            helpers.log(f'count translator episodes fault ex: {ex}')
            return None

    def _annotate_translators(self, titles, ids, directors, premium, post_id, url, current=None, with_counts=True):
        display = list(titles)
        counts = {}
        if with_counts:
            with helpers.busy_dialog():
                for index, translator_id in enumerate(ids):
                    if index >= len(display):
                        break
                    director = None
                    if directors:
                        try:
                            director = directors[index]
                        except Exception:
                            director = None
                    counts[index] = self._count_translator_episodes(post_id, translator_id, url, director)
        for index, translator_id in enumerate(ids):
            if index >= len(display):
                break
            if premium and index < len(premium) and premium[index]:
                display[index] = '%s [%s]' % (display[index], self.language(30019))
            if counts.get(index) is not None:
                display[index] = '%s [%d]' % (display[index], counts[index])
            if current is not None and translator_id == current:
                display[index] = '* %s' % display[index]
        return display

    def select_translator_item(self, uri, via=None, atl=None, strm=None):
        response = self.make_response('GET', uri)
        if not response.text:
            helpers.log('select_translator_item empty response, retrying')
            response = self.make_response('GET', uri)
            if not response.text:
                return
        content_list = common.parseDOM(response.text, "div", attrs={"class": "b-content__main"})
        if not content_list:
            helpers.log("select_translator_item fault parse main content")
            return
        try:
            post_id = common.parseDOM(response.text, "input", attrs={"id": "post_id"}, ret="value")[0]
        except Exception as ex:
            helpers.log(f'select_translator_item fault post_id ex: {ex}')
            return
        titles, ids, directors, premium, active = self._parse_translators(content_list[0])
        if not titles or not ids:
            return
        cached = self._get_cached_translator(post_id, ids)
        atl_mode = (atl or '').lower() == 'true'
        picked_id = None
        if atl_mode:
            # Headless opens never dialog: keep cached choice, else site-active.
            current = cached if cached is not None else active
            helpers.log('select_translator_item atl silent, kept translator %s' % current)
        else:
            is_series = bool(common.parseDOM(response.text, "div", attrs={"id": "simple-episodes-tabs"}))
            display = self._annotate_translators(titles, ids, directors, premium, post_id, uri, cached, is_series)
            dialog = xbmcgui.Dialog()
            index_ = dialog.select(self.language(30006), display)
            if int(index_) >= 0:
                try:
                    picked_name = titles[index_] if index_ < len(titles) else ''
                    HDRezkaCache(self.profile).set_post_translation(post_id, ids[index_], picked_name)
                    helpers.log('select_translator_item saved post %s translator %s' % (post_id, ids[index_]))
                    picked_id = ids[index_]
                except Exception as ex:
                    helpers.log(f'select_translator_item fault save cache ex: {ex}')
        if via == 'menu':
            xbmc.executebuiltin(CONTAINER_REFRESH)
        else:
            try:
                self.show(uri, (atl or '').lower() == 'true', strm)
            except Exception as ex:
                helpers.log(f'select_translator_item fault rebuild ex: {ex}')
                xbmcplugin.endOfDirectory(self.handle, False)
                return
        # site sync is best-effort and always last: never block UI on it.
        if picked_id is not None:
            try:
                self._push_translator_to_site(post_id, picked_id, uri)
            except Exception as ex:
                helpers.log(f'select_translator_item fault push ex: {ex}')

    def _push_translator_to_site(self, post_id, translator_id, url):
        try:
            response = self.make_response('POST', '/ajax/send_watching/?t=', data={
                'id': post_id,
                'action': 'add',
                'translator_id': translator_id,
            }, headers=self._cdn_headers(url)).json()
            helpers.log('send_watching response: %s' % response)
        except Exception as ex:
            helpers.log('send_watching fault ex: %s' % ex)

    def select_translator(self, content, tv_show, post_id, url, idt, action, allow_dialog=False):
        titles, ids, directors, premium, _active = self._parse_translators(content)
        if not titles:
            return tv_show, idt, None
        cached = self._get_cached_translator(post_id, ids)
        if cached is not None:
            idt = cached
        elif allow_dialog and ids and titles:
            display = self._annotate_translators(titles, ids, directors, premium, post_id, url, cached, action != "get_movie")
            dialog = xbmcgui.Dialog()
            index_ = dialog.select(self.language(30006), display)
            if 0 <= int(index_) < len(ids):
                idt = ids[index_]
                try:
                    HDRezkaCache(self.profile).set_post_translation(post_id, idt, titles[index_])
                except Exception as ex:
                    helpers.log(f'select_translator fault save cache ex: {ex}')

        data = {
            "id": post_id,
            "translator_id": idt,
            "action": action
        }
        if directors:
            try:
                director = directors[ids.index(idt)]
            except Exception:
                director = None
            if director:
                data['is_director'] = director

        headers = self._cdn_headers(url)
        try:
            response = self.make_response('POST', CDN_SERIES_URL, data=data, headers=headers).json()
        except Exception as ex:
            helpers.log(f'select_translator fault request ex: {ex}')
            return tv_show, idt, None

        subtitles = None
        try:
            if action == "get_movie":
                playlist = [response["url"]]
                subtitles = helpers.get_subtitles(response)
            else:
                episodes = response["episodes"]
                playlist = common.parseDOM(episodes, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
        except Exception as ex:
            helpers.log(f'select_translator fault playlist ex: {ex}')
            return tv_show, idt, None
        return playlist, idt, subtitles

    def show(self, uri, atl_mode=False, strm=None):
        response = self.make_response('GET', uri)

        if "anubis_challenge" in response.text:
            helpers.log("Anubis challenge detected")

            if not self.solve_anubis(response.text, uri):
                helpers.log("Anubis solve failed")
                return

            response = self.make_response('GET', uri)
            helpers.log("received protection page instead of movie page")
            helpers.log(response.text)
            helpers.log("Solving Anubis")

            if not self.solve_anubis(response.text, uri):
                helpers.log("Anubis failed")
                return

            response = self.make_response('GET', uri)

        content_list = common.parseDOM(
            response.text,
            "div",
            attrs={"class": "b-content__main"}
        )

        if not content_list:
            helpers.log("fault parse main content")
            return

        content = content_list[0]
        image = common.parseDOM(content, "img", attrs={"itemprop": "image"}, ret="src")[0]
        title = common.parseDOM(content, "h1")[0]
        post_id = common.parseDOM(response.text, "input", attrs={"id": "post_id"}, ret="value")[0]
        translator_titles, translator_ids, _directors, translator_premium, translator_active = self._parse_translators(content)
        has_translator_choice = bool(translator_titles and translator_ids)
        idt = translator_active
        if idt is None:
            helpers.log('no active translator found')
            idt = "0"
            try:
                idt = response.text.split("sof.tv.initCDNSeriesEvents")[-1].split("{")[0]
                idt = idt.split(",")[1].strip()
            except Exception as ex:
                helpers.log(f'fault search CDN ex: {ex}')
        if not idt.isdigit():
            helpers.log('fault translator id, using default: %s' % idt)
            idt = "0"
        subtitles = None
        tv_show = common.parseDOM(response.text, "div", attrs={"id": "simple-episodes-tabs"})
        if tv_show:
            if has_translator_choice:
                self._add_translator_item(translator_titles, translator_ids, translator_premium, post_id, idt, uri)
            tv_show, idt, subtitles = self.select_translator(content, tv_show, post_id, uri, idt, "get_episodes", allow_dialog=not atl_mode and self.translator == 'select')
            titles = common.parseDOM(tv_show, "li")
            ids = common.parseDOM(tv_show, "li", ret='data-id')
            seasons = common.parseDOM(tv_show, "li", ret='data-season_id')
            episodes = common.parseDOM(tv_show, "li", ret='data-episode_id')

            for title_, episode_post_id, season_id, episode_id in zip(titles, ids, seasons, episodes):
                if atl_mode:
                    try:
                        season_no = int(season_id)
                        episode_no = int(episode_id)
                    except (TypeError, ValueError):
                        season_no = 0
                        episode_no = 0
                    label = "%s.s%02de%02d" % (title.strip(), season_no, episode_no)
                    episode_title = title
                else:
                    label = f"{title_} ({self.language(30005)} {season_id})"
                    episode_title = title_
                url_episode = uri
                # Library URLs carry ids alone; title/image serve the quality picker only.
                slim = atl_mode
                item_uri = router.build_uri(
                    'play_episode',
                    url=url_episode,
                    post_id=episode_post_id,
                    season_id=season_id,
                    episode_id=episode_id,
                    title=None if slim else episode_title,
                    image=None if slim else image,
                    idt=idt,
                    strm='1' if atl_mode else None,
                )
                item = xbmcgui.ListItem(label)
                item.setArt({'thumb': image, 'icon': image})
                item.setInfo(type='Video', infoLabels={'title': label})
                if has_translator_choice:
                    item.addContextMenuItems(self._translator_menu(uri))
                if self.quality != 'select' or atl_mode:
                    item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, item_uri, item, False if self.quality != 'select' or atl_mode else True)
        else:
            content = [response.text]
            if has_translator_choice:
                self._add_translator_item(translator_titles, translator_ids, translator_premium, post_id, idt, uri)
            # Movie pages are never scanned headless, so asking on miss is safe.
            content, idt, subtitles = self.select_translator(content[0], content, post_id, uri, idt, "get_movie", allow_dialog=True)
            if subtitles is None:
                # when action == get_movie, None is returned only when some exception occurs,
                # so we set the streams_block to default
                streams_match = re.search(r'"streams":"([^"]+)', response.text)
                if not streams_match:
                    helpers.log('fault streams block')
                    return
                streams_block = streams_match.group(1)
            else:
                # success, get selected translator streams
                streams_block = content[0]
            links = parse_streams(streams_block)
            play_info = {
                'post_id': post_id,
                'translator_id': idt,
                'season': 0,
                'episode': 0,
            }
            self.select_quality(links, title, image, subtitles, '1' if strm == '1' else None, play_info)

        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def get_item_additional_info(self, post_id):
        additional = {
            'rating': {
                'site': '',
                'imdb': '',
                'kp': ''
            },
            'age_limit': '',
            'description': ''
        }
        if not self.show_description:
            return additional

        try:
            cached = HDRezkaCache(self.profile).get_bubble(post_id, BUBBLE_CACHE_TTL)
        except Exception as ex:
            helpers.log(f'get bubble cache fault ex: {ex}')
            cached = None
        if cached is not None:
            return cached

        response = self.make_response('POST', '/engine/ajax/quick_content.php', data={
            "id": post_id,
            "is_touch": 1
        })

        try:
            additional['description'] = common.parseDOM(response.text, 'div', attrs={'class': 'b-content__bubble_text'})[0]
        except IndexError:
            helpers.log(f'fault parse description post_id: {post_id}', xbmc.LOGDEBUG)

        try:
            additional['age_limit'] = re.search(r'<b style="color: #333;">(\d+\+)</b>', response.text).group(1)
        except AttributeError:
            helpers.log(f'fault parse age_limit post_id: {post_id}', xbmc.LOGDEBUG)

        try:
            site_rating = common.parseDOM(response.text, 'div', attrs={'class': 'b-content__bubble_rating'})[0]
            additional['rating']['site'] = common.parseDOM(site_rating, 'b')[0]
        except IndexError:
            helpers.log(f'fault parse site rating post_id: {post_id}', xbmc.LOGDEBUG)

        try:
            imdb_rating_block = common.parseDOM(response.text, 'span', attrs={'class': 'imdb'})[0]
            imdb_rating = common.parseDOM(imdb_rating_block, 'b')[0]
            additional['rating']['imdb'] = imdb_rating
            additional['description'] = f'IMDb: {helpers.color_rating(imdb_rating)}\n{additional["description"]}'
        except IndexError:
            helpers.log(f'fault parse imdb rating post_id: {post_id}', xbmc.LOGDEBUG)

        try:
            kp_rating_block = common.parseDOM(response.text, 'span', attrs={'class': 'kp'})[0]
            kp_rating = common.parseDOM(kp_rating_block, 'b')[0]
            additional['rating']['kp'] = kp_rating
            additional['description'] = f' Кинопоиск: {helpers.color_rating(kp_rating)}\n{additional["description"]}'
        except IndexError:
            helpers.log(f'fault parse kp rating post_id: {post_id}', xbmc.LOGDEBUG)

        try:
            HDRezkaCache(self.profile).set_bubble(post_id, additional, BUBBLE_CACHE_TTL)
        except Exception as ex:
            helpers.log(f'set bubble cache fault ex: {ex}')

        return additional

    def history(self):
        words = history.get_history()
        for word in reversed(words):
            uri = router.build_uri('search', keyword=word, main=1)
            item = xbmcgui.ListItem(word)
            item.setArt({'thumb': self.icon, 'icon': self.icon})
            item.addContextMenuItems([(self.language(30015), RUN_PLUGIN_FMT % router.build_uri('history_delete', keyword=word))])
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        xbmcplugin.endOfDirectory(self.handle, True)

    def delete_history(self, keyword):
        if keyword:
            history.delete_from_history(keyword)
            xbmcgui.Dialog().notification(self.addon.getAddonInfo('name'), self.language(30017), self.icon)
        xbmc.executebuiltin(CONTAINER_REFRESH)

    def delete_continue(self, data_id):
        if data_id:
            response = self.make_response('POST', '/engine/ajax/cdn_saves_remove.php', data={'id': data_id})
            helpers.log(f'continues remove response: {response.status_code}')
            xbmcgui.Dialog().notification(self.addon.getAddonInfo('name'), self.language(30018), self.icon)
        xbmc.executebuiltin(CONTAINER_REFRESH)

    def continues(self):
        response = self.make_response('GET', '/continue/')
        genres = common.parseDOM(response.text, "div", attrs={"class": "b-videosaves__list_item"})
        titles = common.parseDOM(genres, "div", attrs={"class": "td title"})
        info = common.parseDOM(genres, "div", attrs={"class": "td info"})
        controls = common.parseDOM(genres, "div", attrs={"class": "td controls"})
        try:
            translator_cache = HDRezkaCache(self.profile)
        except Exception as ex:
            helpers.log(f'continues fault cache ex: {ex}')
            translator_cache = None

        progress_pattern = re.compile(r'^'
                                      r'(?:(.*?)(?=\s*(?:\d+\s*сезон|\d+\s*серия|смотреть|$)))?'
                                      r'(?:\s*(\d+)\s*сезон)?'
                                      r'(?:\s*(\d+)\s*серия)?'
                                      r'(?:\s*(\(.*?\)))?'
                                      r'(?:\s*смотреть\s*ещё\s*(\d+))?'
                                      r'(?:\s*смотреть\s*следующий\s*(\d+))?'
                                      r'.*?$', re.IGNORECASE | re.UNICODE | re.VERBOSE)

        for i, title_html in enumerate(titles):
            try:
                if i >= len(info):
                    continue
                try:
                    year = (common.parseDOM(title_html, "small")[0])[1:5]
                except (IndexError, TypeError):
                    year = ''
                try:
                    link_title = common.parseDOM(title_html, "a")[0]
                except IndexError:
                    continue
                episodes_text = common.stripTags(info[i])
                match = progress_pattern.match(episodes_text)

                result = None
                if match:
                    result = list(match.groups())
                    result = [x.strip() if x and j in (0, 3) else x for j, x in enumerate(result)]
                    result = [x if x and x.strip() else None for x in result]

                episodes = None
                translate = None
                season = None
                episode = None
                episode_new = None
                season_new = None
                if result is not None and len(result) == 6:
                    if result[0] is not None:
                        translate = '(%s)' % result[0]
                    if result[1] is not None:
                        season = result[1]
                    if result[2] is not None:
                        episode = result[2]
                    if result[3] is not None:
                        translate = result[3]
                    if result[4] is not None:
                        episode_new = result[4]
                    if result[5] is not None:
                        season_new = result[5]

                if season and episode:
                    episodes = '[s%se%s]' % (season, episode)
                    if episode_new:
                        episodes = episodes.replace(']', '')
                        episodes = '%s - новых %s в сезоне]' % (episodes, episode_new)
                    if season_new:
                        episodes = episodes.replace(']', '')
                        episodes = '%s - новый %sй сезон]' % (episodes, season_new)

                try:
                    item_link = common.parseDOM(info[i], "a", ret='href')[0]
                except IndexError:
                    try:
                        item_link = common.parseDOM(title_html, "a", ret='href')[0]
                    except IndexError:
                        continue
                if translator_cache is not None:
                    try:
                        show_post_id = re.search(r'/(\d+)-', item_link).group(1)
                        cached_name = translator_cache.get_post_translation_name(show_post_id)
                    except Exception:
                        cached_name = None
                    if cached_name:
                        translate = cached_name
                label = '%s [COLOR=lawngreen](%s)[/COLOR]%s%s' % (
                    link_title,
                    year,
                    '[COLOR=gold]%s[/COLOR]' % translate if translate is not None else '',
                    '[COLOR=cyan]%s[/COLOR]' % episodes if episodes is not None else ''
                )
                item_uri = router.build_uri('show', uri=router.normalize_uri(item_link))
                item = xbmcgui.ListItem(label)
                try:
                    thumb = self._normalize_url(common.parseDOM(title_html, "a", ret='data-cover_url')[0])
                except IndexError:
                    thumb = self.icon
                item.setArt({'thumb': thumb, 'icon': thumb})
                item.setInfo(type='video', infoLabels={'title': label, 'year': year})
                try:
                    save_id = common.parseDOM(controls[i], "a", attrs={"class": "i-sprt delete"}, ret='data-id')[0]
                except (IndexError, TypeError):
                    save_id = None
                menu_items = []
                if save_id:
                    menu_items.append((self.language(30016), RUN_PLUGIN_FMT % router.build_uri('continue_delete', id=save_id)))
                menu_items.extend(self._translator_menu(router.normalize_uri(item_link)))
                item.addContextMenuItems(menu_items)
                is_serial = bool(episodes)
                is_folder = True
                if (self.quality != 'select') and not is_serial:
                    item.setProperty('IsPlayable', 'true')
                    is_folder = False
                xbmcplugin.addDirectoryItem(self.handle, item_uri, item, is_folder)
            except Exception as ex:
                helpers.log(f'continues fault item ex: {ex}')
                continue

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def get_user_input(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(30000))
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            if self.use_transliteration:
                keyword = transliterate.rus(kbd.getText())
            else:
                keyword = kbd.getText()

            history.add_to_history(keyword)

        return keyword

    def search(self, keyword, external):
        helpers.log(f'*** search keyword: {keyword} external: {external}')

        keyword = urllib.parse.unquote_plus(keyword) if (external is not None) else self.get_user_input()
        if not keyword:
            return self.menu()

        params = {
            "do": "search",
            "subaction": "search",
            "q": str(keyword)
        }
        response = self.make_response('GET', '/search/', params=params, cookies={"dle_user_taken": '1'})

        content = common.parseDOM(response.text, "div", attrs={"class": "b-content__inline_items"})
        items = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"})
        post_ids = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"}, ret="data-id")
        link_containers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-link"})
        links = common.parseDOM(link_containers, "a", ret='href')
        titles = common.parseDOM(link_containers, "a")

        for i, name in enumerate(titles):
            info = self.get_item_additional_info(post_ids[i])
            country_divs = common.parseDOM(link_containers[i], "div")
            country_text = country_divs[0] if country_divs else ''
            title = helpers.built_title(name, country_text, **info)
            image = self._normalize_url(common.parseDOM(items[i], "img", ret='src')[0])
            item_uri = router.build_uri('show', uri=router.normalize_uri(links[i]))
            year, country, genre = helpers.get_media_attributes(country_text)
            is_serial = common.parseDOM(items[i], 'span', attrs={"class": "info"})
            item = xbmcgui.ListItem(title)
            item.setArt({'thumb': image, 'icon': image})
            item.addContextMenuItems(self._translator_menu(router.normalize_uri(links[i])))
            info_labels = {
                'title': title,
                'genre': genre,
                'country': country,
                'plot': info['description'],
                'rating': info['rating']['site']
            }
            if year:
                info_labels['year'] = year
            if info['age_limit']:
                info_labels['mpaa'] = info['age_limit']
            item.setInfo(type='video', infoLabels=info_labels)
            is_folder = True
            if (self.quality != 'select') and not is_serial:
                item.setProperty('IsPlayable', 'true')
                is_folder = False
            xbmcplugin.addDirectoryItem(self.handle, item_uri, item, is_folder)

        xbmcplugin.setContent(self.handle, 'movies')
        xbmcplugin.endOfDirectory(self.handle, True)

    def play(self, url, subtitles=None, play_info=None, title=None):
        helpers.log(f'*** play url: {url} subtitles: {subtitles}')

        item = xbmcgui.ListItem(path=url)
        if title:
            osd_title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
            item.setInfo(type='Video', infoLabels={'title': osd_title or title})
        if play_info:
            # HDRezkaPlayer sees only the resolved item: attach all ids here.
            item.setProperty('addon_id', self.id)
            for key, value in play_info.items():
                item.setProperty(key, '%s' % value)
        helpers.set_item_subtitles(item, subtitles)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def play_episode(self, url, post_id, season_id, episode_id, title=None, image=None, idt=None, strm=None, show_id=None):
        if show_id is not None:
            try:
                cached = HDRezkaCache(self.profile).get_post_translation(show_id)
            except Exception as ex:
                helpers.log(f'play_episode fault read cache ex: {ex}')
                cached = None
            if cached is not None:
                idt = cached
        data = {
            "id": post_id,
            "translator_id": idt,
            "season": season_id,
            "episode": episode_id,
            "action": "get_stream"
        }
        headers = {
            "Host": self.domain,
            "Origin": self.url,
            "Referer": url,
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest"
        }
        response = self.make_response('POST', CDN_SERIES_URL, data=data, headers=headers).json()
        data = response["url"]
        subtitles = helpers.get_subtitles(response)
        links = parse_streams(data)
        play_info = {
            'post_id': post_id,
            'translator_id': idt,
            'season': season_id,
            'episode': episode_id,
        }
        self.select_quality(links, title, image, subtitles, strm, play_info)
        xbmcplugin.setContent(self.handle, 'episodes')
        xbmcplugin.endOfDirectory(self.handle, True)

    def _normalize_url(self, item):
        if not item.startswith("http"):
            item = self.url + item
        return item


def main():
    plugin = HdrezkaTV()

    action = sys.argv[2]
    if action == 'authorize':
        actions.authorize(plugin)
    elif action == 'external_config_update':
        actions.external_config_update(plugin)
    else:
        plugin.main(action)

if __name__ == '__main__':
    main()
