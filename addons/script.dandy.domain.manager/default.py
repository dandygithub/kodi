# -*- coding: utf-8 -*-
# Writer (c) 2019-2021, dandy
# Licence: GPL v.3: http://www.gnu.org/licenses/gpl-3.0.html

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import simplejson as json
import XbmcHelpers
common = XbmcHelpers

ID = "script.dandy.domain.manager"
ADDON = xbmcaddon.Addon(ID)
PATH = ADDON.getAddonInfo("path")
HANDLE = int(sys.argv[1]) if (len(sys.argv) > 1) else None
PARAMS = sys.argv[2] if (len(sys.argv) > 2) else None
ICON = ADDON.getAddonInfo("icon")

SETTINGS = ADDON.getSetting("settings") if ADDON.getSetting("settings") else "domain"
PROTOCOL = ADDON.getSetting("protocol") if ADDON.getSetting("protocol") else None

def show_message(msg):
    xbmc.executebuiltin("XBMC.Notification(%s, %s, %s)" % ("MESSAGE", msg, str(5 * 1000)))

REQUEST = {'jsonrpc': '2.0',
           'method': '{0}',
           'params': '{1}',
           'id': 1
           }

def jsonrpc(method, params):
    request = REQUEST
    request['method'] = method
    request['params'] = params
    response = xbmc.executeJSONRPC(json.dumps(request))
    j = json.loads(response)
    return j.get('result')

def get_addons():
    result = jsonrpc("Addons.GetAddons", {'type': 'xbmc.addon.video', 'content': 'video', 'installed': True, 'enabled': True, 'properties': ['name']})
    return result.get("addons"), result.get("limits")

def find_domain_setting(addon):
    setting = None
    domain = None    
    protocol = None
    protocol_value = None

    for item in SETTINGS.split(","):
        domain = addon.getSetting(item)
        if domain:
            setting = item
            break 

    for item in PROTOCOL.split(","):
        protocol_value = addon.getSetting(item)
        if protocol_value:
            protocol = item
            break 

    return setting, domain, protocol, protocol_value

def menu():
    addons, limits = get_addons() 
    for i, addon in enumerate(addons):
        addon_object = xbmcaddon.Addon(addon['addonid'])
        setting, domain, protocol, protocol_value = find_domain_setting(addon_object)
        if setting:
            uri = sys.argv[0] + '?mode=%s&addon=%s' % ("edit", addon['addonid'])
            title = "{0} [COLOR=orange][{1}][/COLOR]".format(addon.get("name"), addon.get("addonid"))
            item = xbmcgui.ListItem(title)
            item.setArt({ 'thumb': ICON, 'icon' : ICON })
            item.setInfo(type='Video', infoLabels={'title': title, 'genre': domain, 'plot': domain})
            xbmcplugin.addDirectoryItem(HANDLE, uri, item, False)
    xbmcplugin.setContent(HANDLE, 'addon')
    xbmcplugin.endOfDirectory(HANDLE, True)

def get_user_input(value, title):
    kbd = xbmc.Keyboard()
    kbd.setDefault(value)
    kbd.setHeading(title)
    kbd.doModal()
    keyword = None
    if kbd.isConfirmed():
        keyword = kbd.getText()
    return keyword

def edit(addon):
    addon_object = xbmcaddon.Addon(addon)
    setting, domain, protocol, protocol_value = find_domain_setting(addon_object)
    if protocol_value:
        protocol_value = get_user_input(protocol_value, "Edit protocol")
    domain = get_user_input(domain, "Edit domain")
    if protocol_value:
        addon_object.setSetting(protocol, protocol_value)
    if domain:
        addon_object.setSetting(setting, domain)

def main():
    if HANDLE:
        params = common.getParameters(PARAMS)
        mode = params['mode'] if 'mode' in params else None
        addon = params['addon'] if 'addon' in params else None
        if (mode == "edit"):
           edit(addon)
        elif (mode is None):
           menu()

if __name__ == '__main__':
    main()
