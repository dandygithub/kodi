import json

from requests.cookies import cookiejar_from_dict
import xbmc


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

def dump_cookies(cookies):
    return json.dumps(dict(cookies))

def load_cookies(src):
    return cookiejar_from_dict(json.loads(src))

def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f'hdrezka: {msg}', level)

def get_subtitles(response):
    subtitles = None
    try:
        subtitles = response["subtitle"].split(',')
        for si in range(len(subtitles)):
            parts = subtitles[si].split(']');
            subtitles[si] = parts[1].replace("\/", "/")
    except Exception as ex:
        log(f'fault decode subtitles ex: {ex}')
    return subtitles

def set_item_subtitles(item, subtitles):
    if subtitles:
        if not isinstance(subtitles, list):
            subtitles = [ subtitles ]

        item.setSubtitles(subtitles) 
