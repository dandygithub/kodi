import xbmc
import urllib, urllib2
import socket

socket.setdefaulttimeout(120)

def get_response(url, headers, values, method):
    if method == 'GET':
        encoded_kwargs = urllib.urlencode(values.items())
        argStr = ""
        if encoded_kwargs:
            if "?" in url:
                argStr = "&%s" %(encoded_kwargs)            
            else:
                argStr = "?%s" %(encoded_kwargs)
        request = urllib2.Request(url + argStr, "", headers)
    else:
        request = urllib2.Request(url, urllib.urlencode(values.items()), headers)
    request.get_method = lambda: method
    return urllib2.urlopen(request).read()

def encode(param):
    try:
        return unicode(param).encode('utf-8')
    except:
        return param

def decode(param):
    try:
        return param.decode('utf-8')
    except:
        return param

def strip(string):
    return common.stripTags(string)
