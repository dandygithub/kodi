# coding: utf-8
# Author: dandy

import urllib, urllib2
import xbmc
import XbmcHelpers
import socket
common = XbmcHelpers

socket.setdefaulttimeout(120)

def get_key(content, content2):
    key = ''
    value = '' 
    try:  
        data = content.split("window['")[-1].split("';")[0]
        value = data.split("'")[2]
        key = content2.split('};n.')[-1].split('=e[')[0] 
    except:
        pass 
    return key, value


def get_access_attrs(content):
    values = {}
    attrs = {}

    script = "http://s9.cdnapponline.com" + common.parseDOM(content, "script", ret="src")[0]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    }
    request = urllib2.Request(script, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()

    attrs['purl'] = '/manifests/video/' + content.split("video_token: '")[-1].split("',")[0]  + "/all"

    values['mw_key'] = response.split('mw_key:"')[-1].split('",')[0] 
    values['ad_attr'] = response.split('ad_attr:')[-1].split(',')[0] 
    values['iframe_version'] = response.split('iframe_version:"')[-1].split('"')[0] 
    values['mw_pid'] = content.split("partner_id: ")[-1].split(",")[0] 
    values['adb'] = 'false'    
    
    values[response.split(',mw_pid:this.options.partner_id,')[-1].split(':this.options.domain_id')[0]] = content.split("domain_id: ")[-1].split(",")[0]     
    
    param = response.split('t,e.')[-1].split('";var')[0]
    values[param.split('="')[0]] = param.split('="')[1]

    param = response.split('window._mw_adb};e.')[-1].split('=window[')[0]
    value = response.split('"]="')[-1].split('"},loadSecondLayer')[0]
    values[param] = value

    #key, value = get_key(content, response) 
    #values[key] = value

    xbmc.log("param=" + repr(values) + " " + repr(attrs))

    return values, attrs
