import requests

import xbmcgui

from helpers import log, busy_dialog, dump_cookies


def authorize(plugin):
    log('*** authorize')

    with busy_dialog():
        login_response = plugin.make_response('POST', '/ajax/login/', data={
            'login_name': plugin.addon.getSetting('username'),
            'login_password': plugin.addon.getSetting('password'),
            'login_not_save': '0'
        })

        data = login_response.json()
        if not data.get('success'):
            log(f'code: {login_response.status_code} text: {login_response.text}')
            xbmcgui.Dialog().ok('Error', data.get('message', 'Fault authorize'))
            return

        cookies = login_response.cookies
        cookies['hdmbbs'] = '1'

        plugin.addon.setSetting('cookies', dump_cookies(cookies))
        xbmcgui.Dialog().notification('Success', 'Authorization completed', xbmcgui.NOTIFICATION_INFO)


def external_config_update(plugin):
    log('*** external_config_update')

    with busy_dialog():
        url = plugin.addon.getSetting('external_config_url')

        log(f'attempt fetch config from: {url}')
        config_response = requests.get(url)
        if not config_response.ok:
            xbmcgui.Dialog().ok('Error', f'status: {config_response.status_code}')
            return

        for key, new_value in config_response.json().items():
            old_value = plugin.addon.getSetting(key)
            if old_value == new_value:
                continue

            log(f'updating config key: "{key}" from: "{old_value}" to: "{new_value}"')
            plugin.addon.setSetting(key, new_value)

        xbmcgui.Dialog().notification('Success', 'Updated config', xbmcgui.NOTIFICATION_INFO)
