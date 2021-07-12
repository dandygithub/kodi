import urllib
import sys
 
from Translit import Translit
import XbmcHelpers
import xbmcgui
import xbmcplugin
import xbmc
import SearchHistory as history

from common import *
from pluginSettings import *

common = XbmcHelpers 
transliterate = Translit()

def search(plugin, keyword, external):
        log("*** search")
        keyword = urllib.unquote_plus(keyword) if (external is not None) else getUserInput()

        handle = getHandleSettings()

        if keyword:
            data = {
                "do": "search",
                "subaction": "search",
                "q": unicode(keyword)
            }
            response = get_response(getUrlSettings() + "/search/", data, cookies={"dle_user_taken": "1"})

            content = common.parseDOM(response.text, "div", attrs={"class": "b-content__inline_items"})
            items = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"})
            post_ids = common.parseDOM(content, "div", attrs={"class": "b-content__inline_item"}, ret="data-id")
            link_containers = common.parseDOM(items, "div", attrs={"class": "b-content__inline_item-link"})
            links = common.parseDOM(link_containers, "a", ret='href')
            titles = common.parseDOM(link_containers, "a")
            country_years = common.parseDOM(link_containers, "div")

            for i, name in enumerate(titles):
                info = plugin.get_item_description(post_ids[i])
                title = "%s %s [COLOR=55FFFFFF](%s)[/COLOR]" % (name, color_rating(info['rating']), country_years[i])
                image = plugin._normalize_url(common.parseDOM(items[i], "img", ret='src')[0])
                link =  getDomProtocolSettings() + "://" + links[i].split("://")[-1]
                uri = sys.argv[0] + '?mode=show&url=%s' % link
                year, country, genre = get_media_attributes(country_years[i])
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(
                    type='video',
                    infoLabels={
                        'title': title,
                        'genre': genre,
                        'year': year,
                        'country': country,
                        'plot': info['description'],
                        'rating': info['rating']
                    }
                )
                is_serial = common.parseDOM(items[i], 'span', attrs={"class": "info"})
                if (getQualitySettings() != 'select') and not is_serial:
                    item.setProperty('IsPlayable', 'true')
                    xbmcplugin.addDirectoryItem(handle, uri, item, False)
                else:
                    xbmcplugin.addDirectoryItem(handle, uri, item, True)

            xbmcplugin.setContent(handle, 'movies')
            xbmcplugin.endOfDirectory(handle, True)
        else:
            plugin.menu()

def getUserInput():
    kbd = xbmc.Keyboard()
    kbd.setDefault('')
    kbd.setHeading(getLanguageSettings()(1000))
    kbd.doModal()
    keyword = None

    if kbd.isConfirmed():
        if getTranslitSettings() == 'true':
            keyword = transliterate.rus(kbd.getText())
        else:
            keyword = kbd.getText()

        history.add_to_history(keyword)

    return keyword