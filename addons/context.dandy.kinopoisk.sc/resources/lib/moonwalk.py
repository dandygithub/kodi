import urllib, urllib2
import json
import re
import socket
import xbmc
import xbmcgui
from videohosts import moonwalk
import XbmcHelpers
common = XbmcHelpers
import tools

socket.setdefaulttimeout(120)

USER_AGENT = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0"

QUALITY_TYPES = (360, 480, 720, 1080)
PLAYLIST_DOMAIN = "moonwalk.cc"
PLAYLIST_DOMAIN2 = "streamblast.cc"

def select_translator(content, url):
    translators = []
    tr_values = []

    data = content.split("translations: [[")[-1].split("]],")[0]
    datal = data.split("],[")
    for item in datal:
        translators.append(item.split(',')[1].replace('"', ''))
        tr_values.append(item.split(',')[0].replace('"', ''))

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

    url_ =  url.replace(url.split("serial/")[-1].split("/iframe")[0], tr_value)

    request = urllib2.Request(url_, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()
    return response, url_

def select_season(data):
    seasons =  data.split("seasons: [")[-1].split("],")[0].split(",")
    values = seasons
    if len(seasons) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select season", seasons)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0    
    if index_ < 0:
        return "", ""
    else:
        return values[index_], str(index_ + 1)


def select_episode(data, url):
    data_, url_ = select_translator(data, url)
    url_ = url_.split('?')[0]
    sindex = None
    eindex = None
    season, sindex = select_season(data_)
    if season == "":
        return "", sindex, eindex

    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    values = {
        "season": season,
        "episode": "1"
    }  
    response = tools.get_response(url_, headers, values, "GET")
    
    series = []
    series_ =  response.split("episodes: [")[-1].split("],")[0].split(",")
    for seria in series_:
        series.append(seria)

    if len(series) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", series)
        if int(index_) < 0:
            return "", sindex, eindex        
    else:
        index_ = 0
    episode = series[index_]
    eindex = str(index_ + 1)
    if episode < 0:
        return "", season, episode

    values = {
        "season": season,
        "episode": episode
    }  
    try: 
        return tools.get_response(url_, headers, values, "GET"), season, episode
    except:
        return "", season, episode


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
    except urllib2.HTTPError, error:
        try:
            url_ = dict(error.info())['location']
            request = urllib2.Request(url_, "", headers)
            request.get_method = lambda: 'GET'
            response = urllib2.urlopen(request).read()
        except:
            return manifest_links, subtitles, season, episode 

    #tvshow
    tvshow = response.split("serial_token: '")[-1].split("',")[0]
    if (tvshow != "null"):
        response, season, episode = select_episode(response, url)
        if response == "":
            return manifest_links, subtitles, season, episode 

    if 'subtitles: {"master_vtt":"' in response:
        subtitles = response.split('subtitles: {"master_vtt":"')[-1].split('"')[0]

    ###################################################
    values, attrs = moonwalk.get_access_attrs(response, url)
    ###################################################

    headers = {}
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    opener.addheaders = [("User-Agent", USER_AGENT)]
    request = urllib2.Request(attrs["purl"], urllib.urlencode(values), headers)
    connection = opener.open(request)
    response = connection.read()
    data = json.loads(response.decode('unicode-escape'))
    playlisturl = data["m3u8"]

    headers = {
        "Host": PLAYLIST_DOMAIN2,
        "Origin": "http://" + PLAYLIST_DOMAIN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    request = urllib2.Request(playlisturl, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()

    urls = re.compile("http:\/\/.*?\n").findall(response)
    for i, url in enumerate(urls):
        manifest_links[QUALITY_TYPES[i]] = url.replace("\n", "")

    return manifest_links, subtitles, season, episode 
   