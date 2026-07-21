import json
from contextlib import contextmanager

from requests.cookies import cookiejar_from_dict

import xbmc

from requests.cookies import RequestsCookieJar, create_cookie


def dump_cookies(cookies):
    data = []

    for cookie in cookies:
        data.append({
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
            "path": cookie.path,
            "secure": cookie.secure,
            "expires": cookie.expires,
        })

    return json.dumps(data)


def load_cookies(src):
    jar = RequestsCookieJar()

    try:
        cookies = json.loads(src)

        for c in cookies:
            jar.set_cookie(
                create_cookie(
                    name=c["name"],
                    value=c["value"],
                    domain=c.get("domain", ""),
                    path=c.get("path", "/"),
                    secure=c.get("secure", False),
                    expires=c.get("expires")
                )
            )

    except Exception as e:
        log(f"load cookies failed: {e}")

    return jar
def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f'hdrezka: {msg}', level)

@contextmanager
def busy_dialog():
    xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    try:
        yield
    finally:
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')


def get_media_attributes(source):
    items = source.split(',')
    if len(items) == 3:
        year, country, genre = items
    else:
        year, genre = items
        country = 'Unknown'
    return year, country, genre


def color_rating(rating):
    if not rating:
        return ''
    rating = float(rating)
    if 0 <= rating < 5:
        return '[COLOR=red][%s][/COLOR]' % rating
    elif 5 <= rating < 7:
        return '[COLOR=yellow][%s][/COLOR]' % rating
    elif rating >= 7:
        return '[COLOR=green][%s][/COLOR]' % rating


def built_title(name, country_years, **kwargs):
    colored_rating = color_rating(kwargs["rating"]["site"])
    colored_info = f'[COLOR=55FFFFFF]{kwargs["age_limit"]} ({country_years})[/COLOR]'
    return f'{name} {colored_rating} {colored_info}'



def get_subtitles(response):
    subtitles = None
    try:
        subtitles = response["subtitle"].split(',')
        for si in range(len(subtitles)):
            parts = subtitles[si].split(']')
            subtitles[si] = parts[1].replace("\/", "/")
    except Exception as ex:
        log(f'fault decode subtitles ex: {ex}')
    return subtitles

def set_item_subtitles(item, subtitles):
    if subtitles:
        if not isinstance(subtitles, list):
            subtitles = [ subtitles ]

        item.setSubtitles(subtitles) 
