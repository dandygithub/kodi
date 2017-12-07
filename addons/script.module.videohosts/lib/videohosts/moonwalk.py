# coding: utf-8
# Author: dandy

import urllib, urllib2
import xbmc
import XbmcHelpers
common = XbmcHelpers

def get_key(content):
    key = ''
    value = '' 
    try:  
        data = content.split('window.')[-1].split("';")[0]
        key = data.split(' ')[0]
        value = data.split("'")[1]
    except:
        pass 
    return key, value


def get_access_attrs(content):
    values = {}
    attrs = {}

    script = "http://s4.cdnapponline.com" + common.parseDOM(content, "script", ret="src")[0]
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

    values['p_domain_id'] = content.split("domain_id: ")[-1].split(",")[0] 
    values['mw_pid'] = content.split("partner_id: ")[-1].split(",")[0] 

    key, value = get_key(content) 

    values[key] = value

    #attrs['X-Access-Level'] = content.split("user_token: '")[-1].split("',")[0] 

    return values, attrs
