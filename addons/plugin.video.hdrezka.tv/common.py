import requests

import xbmc

from constants import *
from pluginSettings import *

def get_response(url, data=None, headers=None, cookies=None, referer='http://www.random.org'):
    if not headers:
        headers = {
            "Host": getDomainSettings(),
            "Referer": referer,
            "User-Agent": USER_AGENT,
        }
    return requests.get(url, params=data, headers=headers, cookies=cookies, proxies=getProxySettings())


def post_response(url, data=None, headers=None, cookies=None, referer='http://www.random.org'):
    if not headers:
        headers = {
            "Host": getDomainSettings(),
            "Referer": referer,
            "User-Agent": USER_AGENT,
        }
    return requests.post(url, data=data, headers=headers, cookies=cookies, proxies=getProxySettings())


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


def log(msg, level=xbmc.LOGNOTICE):
    log_message = u'{0}: {1}'.format('hdrezka', msg)
    xbmc.log(log_message.encode("utf-8"), level)
