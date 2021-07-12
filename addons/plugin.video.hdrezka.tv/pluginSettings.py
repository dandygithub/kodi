import sys

import xbmcaddon

from constants import *

addon = xbmcaddon.Addon(PluginId)

def getLanguageSettings():
    return addon.getLocalizedString

def getDescriptionSettings():
    return addon.getSetting('description')

def getDomainSettings():
    return addon.getSetting('domain')

def getProxySettings():
    if addon.getSetting('use_proxy') == 'false':
        return False
    proxy_protocol = addon.getSetting('protocol')
    proxy_url = addon.getSetting('proxy_url')
    return {
        'http': proxy_protocol + '://' + proxy_url,
        'https': proxy_protocol + '://' + proxy_url
    }

def getQualitySettings():
    return addon.getSetting('quality')

def getTranslatorSettings():
    return addon.getSetting('translator')

def getTranslitSettings():
    return addon.getSetting('translit')

def getHandleSettings():
    return int(sys.argv[1])

def getDomProtocolSettings():
    return addon.getSetting('dom_protocol')

def getUrlSettings():
    return getDomProtocolSettings() + '://' + getDomainSettings()