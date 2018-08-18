# coding: utf-8
# Author: dandy

import urllib, urllib2
import xbmc
import XbmcHelpers
import socket
common = XbmcHelpers

import re
import json
import base64
import binascii
import pyaes

USER_AGENT = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0"

socket.setdefaulttimeout(120)

class EncryptedData:
    def __init__(self):
        pass

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, separators=(',', ':'))

def get_cookies(content):
    cookie = re.compile(r"window\[\'(\w*)\'\]\s=\s\'(\w*)\';").findall(content)[0]
    cookie_header = cookie[0]
    cookie_header = re.sub('\'|\s|\+', '', cookie_header)
    cookie_data = cookie[1]
    cookie_data = re.sub('\'|\s|\+', '', cookie_data)
    cookies = [cookie_header, cookie_data]
    return cookies

def get_access_attrs(content, url):
    values = {}
    attrs = {}

    mw_pid = re.compile(r"partner_id:\s*(\w*),").findall(content)[0]
    p_domain_id = re.compile(r"domain_id:\s*(\w*),").findall(content)[0]

    _mw_adb = False

    video_token = re.compile(r"video_token:\s*\S?\'([0-9a-f]*)\S?\'").findall(content)[0]

    js_path = re.compile(r'script src=\"(.*)\"').findall(content)[0]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    }
    request = urllib2.Request("http://" + url.split('/')[2] + js_path, "", headers)
    request.get_method = lambda: 'GET'
    js_page = urllib2.urlopen(request).read()
    
    e_value = "19f15a0031b8548acfa8da1f2cdf7f73179ac13f3c4938c8bad5a1c93dd8fe06"

    n_value = "79e4add175162a762071a11fe45d249f"

    t = EncryptedData()
    t.a = mw_pid
    t.b = p_domain_id
    t.c = _mw_adb
    #t.d = window_value
    t.e = video_token
    t.f = USER_AGENT

    json_string = t.to_json()

    encrypt_mode = pyaes.AESModeOfOperationCBC(binascii.a2b_hex(e_value), binascii.a2b_hex(n_value))
    encrypter = pyaes.Encrypter(encrypt_mode)
    encrypted = ''
    encrypted += encrypter.feed(json_string)
    encrypted += encrypter.feed()

    attrs['purl'] = "http://" + url.split('/')[2] + "/vs"
    values["q"] = base64.standard_b64encode(encrypted)

    xbmc.log("param=" + repr(values) + " " + repr(attrs))
    return values, attrs


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

def get_access_attrs_old(content):
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
