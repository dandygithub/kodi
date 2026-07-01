import xbmc
import urllib.request, urllib.error, urllib.parse
import socket
import XbmcHelpers as common

socket.setdefaulttimeout(120)

def get_response(url, headers, values, method):
    return decode(get_response_full(url, headers, values, method).read())

def get_response2(url, headers, values, method):
    response = get_response_full(url, headers, values, method)
    return decode(response.read()), response.geturl()

def get_response_full(url, headers, values, method):
    if method == 'GET':
        encoded_kwargs = urllib.parse.urlencode(list(values.items()))
        argStr = ""
        if encoded_kwargs:
            if "?" in url:
                argStr = "&%s" %(encoded_kwargs)            
            else:
                argStr = "?%s" %(encoded_kwargs)
        request = urllib.request.Request(url + argStr, dict(""), headers)
    else:
        request = urllib.request.Request(url, encode(urllib.parse.urlencode(list(values.items()))), headers)
    request.get_method = lambda: method
    return urllib.request.urlopen(request)

def encode(param):
    try:
        return param.encode('utf-8')
    except:
        return param

def decode(param):
    try:
        return param.decode('utf-8')
    except:
        return param

def strip(string):
    return common.stripTags(string)
