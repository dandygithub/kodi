import urllib, urllib2
import json
import re
import socket
import xbmc
import xbmcgui
import XbmcHelpers
common = XbmcHelpers

socket.setdefaulttimeout(120)

QUALITY_TYPES = (360, 480, 720, 1080)


def select_translator(data, url):
    tr_value_curr = url.split('/')[-2]
    tr_select = common.parseDOM(data, "select", attrs={"name": "translate"})[0].replace("\r\n\t", "").replace("<option>", '<option value="' +  tr_value_curr + '">')
    translators = common.parseDOM(tr_select, "option")
    tr_values = common.parseDOM(tr_select, "option", ret="value")

    if len(translators) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select translator", translators)
        if int(index_) < 0:
            index_ = 0    
    else:
        index_ = 0    
    tr_value = tr_values[index_]

    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }

    url_ =  url.replace(tr_value_curr, tr_value)

    request = urllib2.Request(url_, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()
    return response, url_

def select_season(data):
    tvshow = common.parseDOM(data, "select", attrs={"name": "season"})[0]
    seasons = common.parseDOM(tvshow, "option")
    values = common.parseDOM(tvshow, "option", ret="value")
    if len(seasons) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select season", seasons)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0    
    if index_ < 0:
        return ""
    else:
        return values[index_], str(int(seasons[index_].split(" ")[-1]))


def select_episode(data, url):
    sindex = None
    eindex = None
    data_, url_ = select_translator(data, url)

    url_ = url_.split("?")[0]
    season, sindex = select_season(data_)
    if season == "":
        return "", sindex, eindex

    headers = {
        "Referer": url_,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    values = {
        "season": season
    }  
    encoded_kwargs = urllib.urlencode(values.items())
    argStr = "?%s" %(encoded_kwargs)
    try: 
        request = urllib2.Request(url_ + argStr, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
    except:
        return "", sindex, eindex

    #iframe = "http:" + common.parseDOM(response, "iframe", ret="src")[0]        
    #try: 
    #    request = urllib2.Request(iframe, "", headers)
    #    request.get_method = lambda: 'GET'
    #    response = urllib2.urlopen(request).read()
    #except:
    #    return "", sindex, eindex

    tvshow = common.parseDOM(response, "select", attrs={"name": "episode"})[0]
    series = common.parseDOM(tvshow, "option")
    evalues = common.parseDOM(tvshow, "option", ret="value")

    if len(series) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", series)
        if int(index_) < 0:
            return "", sindex, eindex
    else:
        index_ = 0  
    episode = evalues[index_]
    eindex = str(int(series[index_].split(" ")[-1]))
    
    if index_ < 0:
        return "", sindex, eindex

    values2 = {
        "season": season,
        "e": episode
    }  
    encoded_kwargs = urllib.urlencode(values2.items())
    argStr = "?%s" %(encoded_kwargs)

    try: 
        request = urllib2.Request(url + argStr, "", headers)
        request.get_method = lambda: 'GET'
        #response = urllib2.urlopen(request).read()
        return urllib2.urlopen(request).read(), sindex, eindex
    except:
        return "", sindex, eindex
    #iframe = "http:" + common.parseDOM(response, "iframe", ret="src")[0]        
    #try: 
    #    request = urllib2.Request(iframe + argStr, "", headers)
    #    request.get_method = lambda: 'GET'
    #    return urllib2.urlopen(request).read(), sindex, eindex
    #except:
    #    return "", sindex, eindex


def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    try: 
        request = urllib2.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
    except:
        return manifest_links, subtitles, season, episode 

    #tvshow
    tvshow = common.parseDOM(response, "select", attrs={"name": "season"})
    if tvshow:
        response, season, episode = select_episode(response, url)
        if response == "":
            return manifest_links, subtitles, season, episode

    #url_ = common.parseDOM(response, "iframe", ret="src")[0]
    #try: 
    #    request = urllib2.Request(url_, "", headers)
    #    request.get_method = lambda: 'GET'
    #    response = urllib2.urlopen(request).read()
    #except:
    #    return manifest_links, subtitles, season, episode 

    data = response.split("media: [")[-1].split("]")[0]
    data = data.split('},{')
    for i, item in enumerate(data):
        url_ = "http:" + item.split("url: '")[-1].split("'")[0]
        manifest_links[QUALITY_TYPES[i]] = url_ + "|Referer="+url_;

    return manifest_links, subtitles, season, episode 
   