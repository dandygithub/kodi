import sys
import urllib
from operator import itemgetter

import XbmcHelpers
import xbmcgui
import xbmcplugin

from constants import *
from common import *
from pluginSettings import *

common = XbmcHelpers

def selectQuality(plugin, links, title, image, subtitles=None):
    lst = sorted(links.iteritems(), key=itemgetter(0))
    i = 0
    quality_prev = 360
    qualitySetting = getQualitySettings()
    for quality, link in lst:
        i += 1
        if qualitySetting != 'select':
            if quality > int(qualitySetting[:-1]):
                plugin.play(links[quality_prev], subtitles)
                break
            elif len(lst) == i:
                plugin.play(links[quality], subtitles)
        else:
            film_title = "%s (%s)" % (title, str(quality) + 'p')
            uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote(link)
            item = xbmcgui.ListItem(film_title, iconImage=image)
            item.setInfo(
                type='Video',
                infoLabels={'title': film_title, 'overlay': xbmcgui.ICON_OVERLAY_WATCHED, 'playCount': 0}
            )
            item.setProperty('IsPlayable', 'true')
            plugin.set_item_subtitles(item, subtitles)
            xbmcplugin.addDirectoryItem(getHandleSettings(), uri, item, False)
        quality_prev = quality

def selectTranslator3(plugin, content, tvshow, post_id, url, idt, action):
    try:
        div = common.parseDOM(content, 'ul', attrs={'id': 'translators-list'})[0]
    except:
        return tvshow, idt, None
    titles = common.parseDOM(div, 'li', ret='title')
    ids = common.parseDOM(div, 'li', ret="data-translator_id")
    if len(titles) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select(getLanguageSettings()(1006), titles)
        if int(index_) < 0:
            index_ = 0
    else:
        index_ = 0
    idt = ids[index_]

    data = {
        "id": post_id,
        "translator_id": idt,
        "action": action
    }
    is_director = common.parseDOM(div, 'li', attrs={'data-translator_id': idt}, ret='data-director')
    if is_director:
        data['is_director'] = is_director[0]

    headers = {
        "Host": getDomainSettings(),
        "Origin": "http://" + getDomainSettings(),
        "Referer": url,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest"
    }

    #{"success":true,"message":"","url":"[360p]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/3dxox.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/61e68929526165ffb2e5483777a4bd94:2020101118\/8\/8\/1\/3\/3\/3dxox.mp4,[480p]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/ppjm0.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/6498b090482768d1433d456b2e35c46a:2020101118\/8\/8\/1\/3\/3\/ppjm0.mp4,[720p]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/0w0az.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/b10164963f454ad391b2a13460568561:2020101118\/8\/8\/1\/3\/3\/0w0az.mp4,[1080p]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/n9qju.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/b8a860d0938b593ed4b64723944b9a12:2020101118\/8\/8\/1\/3\/3\/n9qju.mp4,[1080p Ultra]https:\/\/stream.voidboost.cc\/8\/8\/1\/3\/3\/ddddfc45662e813d93128d783cb46e7f:2020101118\/4l9xx.mp4:hls:manifest.m3u8 or https:\/\/stream.voidboost.cc\/13c067a1dcd54be75007a74bde421b17:2020101118\/8\/8\/1\/3\/3\/4l9xx.mp4","quality":"480p","subtitle":"[\u0420\u0443\u0441\u0441\u043a\u0438\u0439]https:\/\/static.voidboost.com\/view\/BmdZqxHeI9zXhhEWUUP70g\/1602429855\/8\/8\/1\/3\/3\/c1lz5sebdx.vtt,[\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430]https:\/\/static.voidboost.com\/view\/F8mGgsIZee6XMjvtXSojhQ\/1602429855\/8\/8\/1\/3\/3\/f0zfov3en4.vtt,[English]https:\/\/static.voidboost.com\/view\/enBDXHLd9y6OByIGY8AiZQ\/1602429855\/8\/8\/1\/3\/3\/ut8ik78tq5.vtt","subtitle_lns":{"off":"","\u0420\u0443\u0441\u0441\u043a\u0438\u0439":"ru","\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430":"ua","English":"en"},"subtitle_def":"ru","thumbnails":"\/ajax\/get_cdn_tiles\/0\/32362\/?t=1602170655"}

    response = post_response(getUrlSettings() + "/ajax/get_cdn_series/", data, headers).json()

    subtitles = None
    if (action == "get_movie"):
        playlist = [response["url"] ]
        subtitles = plugin.get_subtitles(response)
    else:
        seasons = response["seasons"]
        episodes = response["episodes"]
        playlist = common.parseDOM(episodes, "ul", attrs={"class": "b-simple_episodes__list clearfix"})
    return playlist, idt, subtitles