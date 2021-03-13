from sys import argv
from urllib import parse


def build_uri(mode, **params):
    uri = {'mode': mode}
    for key, value in params.items():
        if not value:
            continue
        uri[key] = value
    return argv[0] + '?' + parse.urlencode(uri)


def parse_uri(src):
    return dict(parse.parse_qsl(parse.urlsplit(src).query))


def normalize_uri(item):
    return parse.urlsplit(item).path
