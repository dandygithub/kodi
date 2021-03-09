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


def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f'hdrezka: {msg}', level)
