import urllib, urllib2
import json
import re
import socket
import xbmc
import xbmcgui
from videohosts import moonwalk
import XbmcHelpers
common = XbmcHelpers

socket.setdefaulttimeout(120)

def select_season(data):
    tvshow = common.parseDOM(data, "div", attrs={"class": "serial-seasons-box"})[0]
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
        return values[index_], str(index_ + 1)


def select_episode(data, url):
    sindex = None
    eindex = None

    season, sindex = select_season(data)
    if season == "":
        return "", sindex, eindex

    tvshow = common.parseDOM(data, "div", attrs={"class": "serial-panel"})
    episodesbox = common.parseDOM(tvshow[0], "div", attrs={"class": "season-" + season})[0]
    episodes = common.parseDOM(episodesbox, "option")
    urls = common.parseDOM(episodesbox, "option", ret="value")

    if len(episodes) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", episodes)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0  
    eurl = "http:" + urls[index_]
    eindex = str(index_ + 1)
    if index_ < 0:
        return "", sindex, eindex

    xbmc.log("eurl=" + repr(eurl))       

    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    try: 
        request = urllib2.Request(eurl, "", headers)
        request.get_method = lambda: 'GET'
        return urllib2.urlopen(request).read(), sindex, eindex
    except:
        return "", sindex, eindex


def get_attrs(content):
    values = {}
    attrs = {}

    values['domain'] = "kodik.biz"
    values['type'] = content.split("type: '")[-1].split("',")[0] 
    values['hash'] = content.split("hash: '")[-1].split("',")[0] 
    values['id'] = content.split("id: '")[-1].split("',")[0] 

    return values, attrs


def parse_alt(data, urlm, season, episode):
    manifest_links = {}
    subtitles = None

    playerbox = common.parseDOM(data, "div", attrs={"class": "player_box"})[0]
    url = common.parseDOM(playerbox, "iframe", ret="src")[0]
    playlist_domain = url.split("http://")[-1].split("/")[0]

    headers = {
        "Referer": urlm,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    request = urllib2.Request(url, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()

    ###################################################
    values, attrs = moonwalk.get_access_attrs(response)
    ###################################################

    headers = {
        "Host": playlist_domain,
        "Origin": "http://" + playlist_domain,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
        "Referer": url,
        "X-Requested-With": "XMLHttpRequest",
    }
    headers.update(attrs)

    request = urllib2.Request('http://' + playlist_domain + attrs['purl'], urllib.urlencode(values), headers)
    response = urllib2.urlopen(request).read()

    data = json.loads(response.decode('unicode-escape'))
    playlisturl = data['mans']['manifest_m3u8']

    headers = {
        "Host": "streamblast.cc",
        "Origin": "http://video.kodik.name",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    request = urllib2.Request(playlisturl, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()

    urls = re.compile("http:\/\/.*?\n").findall(response)
    for i, url in enumerate(urls):
        manifest_links[QUALITY_TYPES[i]] = url.replace("\n", "")

    return manifest_links, subtitles, season, episode, 1


def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    headers = {
        "Host": "kodik.cc",
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }

    try: 
        request = urllib2.Request(url.split("?")[0], "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
    except:
        return manifest_links, subtitles, season, episode, 0

    iframe = "http:" + response.split('iframe.src = "')[-1].split('";\n')[0]
    try: 
        request = urllib2.Request(iframe, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
    except:
        return manifest_links, subtitles, season, episode, 0

    #tvshow
    div = common.parseDOM(response, "div", attrs={"class": "get_code_main"})[0]
    
    if div:
        iframe = common.parseDOM(div,  "input", ret="value")[0]
        iframe = iframe.split('<iframe src="')[-1].split('"')[0]    
        request = urllib2.Request(iframe, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
        #tvshow
        tvshow = common.parseDOM(response, "div", attrs={"class": "serial-panel"})
        if tvshow:
            response, season, episode = select_episode(response, url)
            if response == "":
                return manifest_links, subtitles, season, episode, 0
        else:
            iframe = "http:" + response.split('iframe.src = "')[-1].split('";\n')[0]
            try: 
                request = urllib2.Request(iframe, "", headers)
                request.get_method = lambda: 'GET'
                response = urllib2.urlopen(request).read()
            except:
                return manifest_links, subtitles, season, episode, 0

    values, attrs = get_attrs(response)

    headers = {
        "Host": "kodik.cc",
        "Origin": "http://kodik.cc",
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    try: 
        request = urllib2.Request("http://kodik.cc/get-video", urllib.urlencode(values), headers)
        request.get_method = lambda: 'POST'
        response = urllib2.urlopen(request).read()
    except:
        try:
            return parse_alt(response, url, season, episode)
        except:
            return manifest_links, subtitles, season, episode, 0

    urls = []
    qualities = []
    pid = 0
    if ('"links"' in response):
        json_playlist = json.loads(response)
        for i, item in enumerate(json_playlist["links"]):
            item2 = json_playlist["links"][item]
            qualities.append(item)
            urls.append(item2[0]["src"])
    else:
        link = response.split('"link":"')[-1].split('","')[0]
        if not ("http:" in link):
            link = "http:" + link

        headers = {
            "Referer": url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
        }
        request = urllib2.Request(link, "", headers)
        request.get_method = lambda: 'GET'
        try:
            response = urllib2.urlopen(request).read()
        except urllib2.HTTPError, error:
            link = dict(error.info())['location']
            request = urllib2.Request(url_, "", headers)
            request.get_method = lambda: 'GET'
            response = urllib2.urlopen(request).read()
        if "http:" in response:
            pid = 1
            qualities = ["360", "480", "720", "1080"]
            urls_ = re.compile("http:\/\/.*?\n").findall(response)
            for i, urlq in enumerate(urls_):
                urls.append(urlq.replace("\n", ""))
        else:
            urls_ = re.compile("\.\/.*?\.m3u8").findall(response)
            for i, urlq in enumerate(urls_):
                urls.append(link.replace("hls.m3u8",  urlq.replace("./", "")))
                qualities.append(urlq.replace("./", "").split(".")[0])

    for i, urlq in enumerate(urls):
        manifest_links[qualities[i]] = urlq

    return manifest_links, subtitles, season, episode, pid
   