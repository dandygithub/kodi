#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib, urllib2, sys, socket
import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import XbmcHelpers
import json
import datetime, time
from resources.lib.decoder import decoder

socket.setdefaulttimeout(120)
common = XbmcHelpers

class Tivix():
    def __init__(self):
        self.id = 'plugin.video.tivix.net'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.time_zone = int(self.addon.getSetting('time_zone'))
        self.use_epg = self.addon.getSetting('epg') if self.addon.getSetting('epg') else "true"

        self.language = self.addon.getLocalizedString
        self.handle = int(sys.argv[1])
        self.url = 'http://tivix.co'

        if (self.use_epg == "true"):
            self.epg = self.loadEPG()

    def main(self):
        params = common.getParameters(sys.argv[2])
        mode = url = None
        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        url2 = urllib.unquote_plus(params['url2']) if 'url2' in params else None
        page = params['page'] if 'page' in params else 1
        image = urllib.unquote_plus(params['image']) if 'image' in params else self.icon
        name = urllib.unquote_plus(params['name']) if 'name' in params else None
        cid = params['cid'] if 'cid' in params else None

        if mode == 'play':
            self.play(url, url2)
        if mode == 'show':
            self.show(url, image, name)
        if mode == 'index':
            self.index(url, page)
        if mode == 'search':
            self.search(url)
        if mode == 'epg':
            self.getEPG(cid, name, image)
        elif mode == None:
            self.menu()

    def menu(self):
        uri = sys.argv[0] + '?mode=%s&url=%s' % ("search", self.url)
        item = xbmcgui.ListItem("[COLOR=FF00FF00]%s[/COLOR]" % self.language(1000), thumbnailImage=self.icon)
        xbmcplugin.addDirectoryItem(self.handle, uri, item, True)
        if (self.use_epg == "true"):
            uri = sys.argv[0] + '?mode=%s' % ("epg")
            item = xbmcgui.ListItem("[COLOR=FF7B68EE]%s[/COLOR]" % self.language(1005), thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        self.genres()

    def parse(self, data, url = '', page = 0, filter = None):
        content = common.parseDOM(data, "div", attrs={"id": "dle-content"})
        pagenav = common.parseDOM(data, "div", attrs={"class": "bot-navigation"}) 
        
        boxes = common.parseDOM(content, "div", attrs={"class": "all_tv"})
        links = common.parseDOM(boxes, "a", ret='href')
        titles = common.parseDOM(boxes, "a", ret='title')
        if not titles:
            titles = common.parseDOM(content, "div", attrs={"class": "all_tv"}, ret='title')
        images = common.parseDOM(boxes, "img", ret='src')
        items = 0

        for i, title in enumerate(titles):
            if (not filter) or (title[:len(filter)].upper() == filter.upper()):
                items += 1

                if links[i] == "http://tivix.co/263-predlozheniya-pozhelaniya-zamechaniya-po-saytu.html":
                    continue

                image = self.url + images[i]

                uri = sys.argv[0] + '?mode=show&url=%s&name=%s&image=%s' % (links[i], title, image)
                item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
                item.setInfo(type='Video', infoLabels={'title': title, 'plot': title})
                #item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        if pagenav and (not (items < 119)):
            uri = sys.argv[0] + '?mode=%s&url=%s&page=%s' % ("index", url, str(int(page) + 1))
            item = xbmcgui.ListItem('%s' % self.language(1003), iconImage=self.icon, thumbnailImage=self.icon)
            item.setInfo(type='Video', infoLabels={'title': 'ЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯ'})
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.handle, 'tvshows')
        xbmcplugin.endOfDirectory(self.handle, True)


    def index(self, url, page):
        page_url = self.url if page == 0 else "%s/page/%s/" % (url, str(int(page)))

        response = common.fetchPage({"link": page_url})

        self.parse(response["content"], url, page)

    def loadEPG(self):
        url = 'http://tivix.co/engine/api/getChannelList.php'
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Host": "tivix.co", 
            "Referer": "http://tivix.co/chto-seychas-na-tv.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        request = urllib2.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
        channels = json.loads(response)
#{"11":{"title":"\u0421\u0422\u0421","image_url":"http:\/\/tivix.co\/uploads\/posts\/2016-04\/1461317169_sts.png","id":"11","alt_name":"sts","cat":"29,27,24,16,17","tv_link":"https:\/\/tv.mail.ru\/channel\/1112\/73\/"},        

        url = 'http://s.programma.space/channels/tivix/program/nearest/'
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Host": "schedule.tivix.co",
            "Origin": "http://tivix.co",
            "Referer": "http://tivix.co/chto-seychas-na-tv.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
        }
        try:
            request = urllib2.Request(url, "", headers)
            request.get_method = lambda: 'GET'
            response = urllib2.urlopen(request).read()
            data = json.loads(response)
        except:
            data = json.loads("{}")
#{"167":[{"name":"\u041b\u0435\u0442\u0430\u044e\u0449\u0438\u0435 \u0437\u0432\u0435\u0440\u0438","start_at":"2017-04-01 16:04:00","date":"2017-04-01 00:00:00"},{"name":"\u0410\u043a\u0430\u0434\u0435\u043c\u0438\u044f \u0421\u0442\u0435\u043a\u043b\u044f\u0448\u043a\u0438\u043d\u0430","start_at":"2017-04-01 16:14:00","date":"2017-04-01 00:00:00"},{"name":"\u0421\u0430\u043b\u044e\u0442 \u0442\u0430\u043b\u0430\u043d\u0442\u043e\u0432","start_at":"2017-04-01 16:28:00","date":"2017-04-01 00:00:00"},{"name":"\u0420\u043e\u0434\u0438\u043b\u0441\u044f \u0426\u0430\u0440\u044c","start_at":"2017-04-01 19:34:00","date":"2017-04-01 00:00:00"},{"name":"\u041a\u0440\u0430\u0441\u043d\u0430\u044f \u0428\u0430\u043f\u043e\u0447\u043a\u0430","start_at":"2017-04-01 19:58:00","date":"2017-04-01 00:00:00"}],

        for channelid in channels:
            try:
                channels[channelid]["epg"] = data[channelid]
            except:
                pass
        return channels

    def getLocalTime(self, epgstart, epgend):
        current = False
        duration = 0
        epgformat = u'%Y-%m-%d %H:%M:%S'
        time_ = datetime.datetime(*(time.strptime(epgstart, epgformat)[:6])) + datetime.timedelta(hours = self.time_zone)
        timeend = datetime.datetime(*(time.strptime(epgend, epgformat)[:6])) + datetime.timedelta(hours = self.time_zone)
        epgtoday = datetime.datetime.today()
        duration = (timeend - epgtoday).seconds
        epgcolor = "FFFFFFFF"
        if epgtoday > timeend:
            epgcolor = "55FFFFFF"
        if (epgtoday >= time_) and (epgtoday < timeend):
            epgcolor = "FF00FF00"
            current = True            
        return '{:%H:%M}'.format(time_), epgcolor, current, duration

    def addEPGItems(self, epgbody, image):
        currname = ''
        currduration = 0 
        listItems = [] 
        for i, epg in enumerate(epgbody): 
            uri = sys.argv[0] + '?'
            end_at = epgbody[i+1]['start_at'] if i+1 < len(epgbody) else '2099-01-01 00:00:00' 
            time, color, current, duration = self.getLocalTime(epg['start_at'], end_at)
            if current == True:
                currname = epg['name']           
                currduration = duration
            item = xbmcgui.ListItem("[I][COLOR=%s]%s %s[/COLOR][/I]" % (color, time, epg['name']),  iconImage=image, thumbnailImage=image)
            listItems.append((uri, item, False)) 
        return currname, currduration, listItems

    def getEPG(self, cid = None, cname = None, image = ''):
        currname = ''
        duration = 0 
        listItems = [] 
        try:
            if cname: 
                if cid:
                    epgbody = self.epg[cid]['epg']
                    currname, duration, listItems = self.addEPGItems(epgbody, image)
            elif cid: 
                epgbody = self.epg[cid]['epg']
                currname, duration, listItems = self.addEPGItems(epgbody, image)
                xbmcplugin.addDirectoryItems(self.handle, listItems)
            else:
                for channelid in self.epg:
                    channelbody = self.epg[channelid]
                    uri = sys.argv[0] + '?mode=epg&cid=%s&image=%s' % (channelid, channelbody['image_url'])
                    item = xbmcgui.ListItem("%s" % channelbody['title'],  iconImage=channelbody['image_url'], thumbnailImage=channelbody['image_url'])
                    item.setInfo(type='Video', infoLabels={'title': channelbody['title']})
    
                    commands = []
                    uricmd = sys.argv[0] + '?mode=show&url=%s&name=%s&image=%s' % (self.url + "/" + channelid + "-" + channelbody['alt_name'] + ".html", channelbody['title'], channelbody['image_url'])
                    commands.append(('[COLOR=FF00FF00]' + self.language(1006) + '[/COLOR]', "Container.Update(%s)" % (uricmd), ))
                    item.addContextMenuItems(commands)

                    xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE)
        except:
            pass
        if cname == None:
            xbmcplugin.setContent(self.handle, 'files')
            xbmcplugin.endOfDirectory(self.handle, True)

        return currname, duration, listItems


    def show(self, link, image, name):
        response = common.fetchPage({"link": link})
        cid = link.split(self.url + "/")[-1].split("-")[0]
        streams = self.getStreamURL(response['content'])
        if streams:
            description = self.strip(response['content'].split("<!--dle_image_end-->")[1].split("<div")[0])
            currname = '' 
            duration = ''
            #description = common.parseDOM(response['content'], "meta", attrs={"name": "description"}, ret = "content")[0]
            if (self.use_epg == "true"):
                currname, duration, listItems = self.getEPG(cid = cid, cname=name, image=image)
            uri = sys.argv[0] + '?mode=play&url=%s&url2=%s' % (urllib.quote_plus(streams[0]), link)
            item = xbmcgui.ListItem("[COLOR=FF7B68EE]%s[/COLOR]" % self.language(1004),  iconImage=image, thumbnailImage=image)
            item.setInfo(type='Video', infoLabels={'title': currname if currname != '' else name, 'plot': description, 'duration': duration})
            item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(self.handle, uri, item, False)
    
            if (self.use_epg == "true"):
                xbmcplugin.addDirectoryItems(self.handle, listItems)
    
            xbmcplugin.setContent(self.handle, 'files')
            xbmcplugin.endOfDirectory(self.handle, True)

    def genres(self):
        response = common.fetchPage({"link": self.url})
        menus = common.parseDOM(response["content"], "div", attrs={"class": "menuuuuuu"})

        for menu in menus:
            titles = common.parseDOM(menu, "a")
            links = common.parseDOM(menu, "a", ret="href")

            for i, link in enumerate(links):
                uri = sys.argv[0] + '?mode=index&url=%s' % urllib.quote_plus(self.url+link)
                item = xbmcgui.ListItem(titles[i], iconImage=self.icon, thumbnailImage=self.icon)
                xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def parseObfusc(self, data):
#;eval(function(w,i,s,e){for(s=0;s<w.length;s+=2){i+=String.fromCharCode(parseInt(w.substr(s,2),36));}return i;}('1b1b0d0a1n2t3a2p30142u39322r382x3332143b182x1837182t153f2u333614371p1c1n371o3b1a302t322v382w1n37171p1e153f2x171p2b38362x322v1a2u3633311v2w2p361v332s2t14342p36372t213238143b1a37392q3738361437181e15181f1i15151n3h362t383936320w2x1n3h14131d2q1d2q1c2s1c2p1318131318131318131315151n1n2t3a2p30142u39322r382x3332143b182x1837182t153f2u333614371p1c1n371o3b1a302t322v382w1n37171p1e153f2x171p2b38362x322v1a2u3633311v2w2p361v332s2t14342p36372t213238143b1a37392q3738361437181e15181f1i15151n3h362t383936320w2x1n3h14131d2q1d2q1c2s1c2p1d321e381f2p1e341f1c1d1g1e391f1l1f1e1e361f1k1e3c1f1f1f1e1d1g1f2q1d1k1e3c1d1k1f1j1d1k1e381d1h1f2u1e391f1f1f1i1d1g1f1j1d341d2r1d321f1j1d331f2q1d2p1f1c1e381f1e1e3a1f1k1e3b1d321f1j1d1j1d341d2t1d1h1f2u1e3c1d1j1d341e2q1f1k1f1i1e3c1f1e1e3a1d2p1e391f1i1f1f1f1d1d3a1e3b1e341f1i1d3a1f1f1e371e381d1g1f1g1e341f1i1f1j1e381e1d1f1e1f1k1d1g1f2q1d2p1f1j1f1l1e351f1j1f1k1f1i1d1g1f1j1d1k1d2t1d1h1d1k1d2u1d2x1d1h1d1h1d321f2w1f1i1e381f1k1f1l1f1i1f1e1c3b1e3c1d321f2w1d1g1d1f1d2s1e351d2s1e351d2r1e371d2r1e341d1f1d1k1d1f1d1f1d1k1d1f1d1f1d1k1d1f1d1f1d1h1d1h1d321318131318131318131315151n','','',''));; ;eval(function(w,i,s,e){var lIll=0;var ll1I=0;var Il1l=0;var ll1l=[];var l1lI=[];while(true){if(lIll<5)l1lI.push(w.charAt(lIll));else if(lIll<w.length)ll1l.push(w.charAt(lIll));lIll++;if(ll1I<5)l1lI.push(i.charAt(ll1I));else if(ll1I<i.length)ll1l.push(i.charAt(ll1I));ll1I++;if(Il1l<5)l1lI.push(s.charAt(Il1l));else if(Il1l<s.length)ll1l.push(s.charAt(Il1l));Il1l++;if(w.length+i.length+s.length+e.length==ll1l.length+l1lI.length+e.length)break;}var lI1l=ll1l.join('');var I1lI=l1lI.join('');ll1I=0;var l1ll=[];for(lIll=0;lIll<ll1l.length;lIll+=2){var ll11=-1;if(I1lI.charCodeAt(ll1I)%2)ll11=1;l1ll.push(String.fromCharCode(parseInt(lI1l.substr(lIll,2),36)-ll11));ll1I++;if(ll1I>=l1lI.length)ll1I=0;}return l1ll.join('');}('33f8b3q012c2e122b3b322v3w24112o241v392215312s0c3b1x1y2c11113s2q233c1z0x1g2531142t211o162137211g273x2a1735141i12313s181627353519293l1k1c1b1g1l1l101y2u103l301a2c212j3r2e1b2e181b1l2x102j1w2d2r1o1t1d1g1k1h1i1e1m1d2b3i282u2f17123x2g3q1c1f2b361q1m','7ab1db3x1z3z2o3y2d221w1a3t3b3q3w39383q29232q1z3c07041z3e3e153z2s0c3b1x143o01141w1z0o143q251z1m3x3c3s0w32141o03132c341m1o3516241x331a191d1f1d1b1a1c3t39181a3u3x2u1q2c3f2g3a2k2j2w361d1c2v172w1h1b1g1i2h1b1h1j2f1f25193v2c3c2e2b203q292g2y372c1q14','cb5d7273c111z193y1q1o23233c32293124333s3u3o253c1x0z0o113139252q1z3c0706393x3q1m253w141g3s35343934013x3535163z103o271g1939123s14371c1i1f1e191l1c3f232b3g1q38392w3q1d223h232e2a371e1w2x141j2w2e2f2b1g1u1h1k1h1s1i1r1h2d3d171h2d3r182b2e1t2d222u121','334ff177903c72644e82a06d97c36bfe'));
#;eval(function(w,i,s,e){for(s=0;s<w.length;s+=2){i+=String.fromCharCode(parseInt(w.substr(s,2),36));}return i;}('1b1b0d0a','','',''));;eval(function(w,i,s,e){for(s=0;s<w.length;s+=2){i+=String.fromCharCode(parseInt(w.substr(s,2),36));}return i;}('1b1b0d0a1n2t3a2p30142u39322r382x3332143b182x1837182t153f2u333614371p1c1n371o3b1a302t322v382w1n37171p1e153f2x171p2b38362x322v1a2u3633311v2w2p361v332s2t14342p36372t213238143b1a37392q3738361437181e15181f1i15151n3h362t383936320w2x1n3h14131d2q1d2q1c2s1c2p1318131318131318131315151n','','',''));
        data = data.split("l1ll.join('');}('")[-1].split("'))")[0]
        arr = data.split("','")
        play = decoder(arr[0], arr[1], arr[2], arr[3])
        return play

    def getStreamURL(self,  dataprev):
        streams = []
        try:
            url = common.parseDOM(dataprev, "span", attrs={"id": "srces"})[0]
#            data = common.parseDOM(dataprev, "div", attrs={"class": "tab-pane fade"})[0].replace('\n', '')
#            data = self.parseObfusc(data)
#            data = self.parseObfusc(data)
#            arrdata = data.split(';eval')
#            data = self.parseObfusc(arrdata[2])
#            if "http://" in data:
#                url = "http://" + data.split("http://")[-1].split("');")[0].split("'};")[0]
#            else:
#                url = "rtmp://" + data.split("rtmp://")[-1].split("'};")[0]
            streams.append(url)
        except:
            self.showErrorMessage("The channel is not available")

        return streams

    def play(self, stream, url_main):
        if 'm3u8' in stream:
            print "M3U8"
            url = stream
        else:
            print "RTMP"
            url = stream
            url += " swfUrl=http://tivix.co/templates/Default/style/uppod.swf"
            url += " pageURL=http://tivix.co"
            url += " swfVfy=true live=true"

        try:         
            item = xbmcgui.ListItem(path = url + "|Referer="+url_main)
            xbmcplugin.setResolvedUrl(self.handle, True, item)
        except:
            self.showErrorMessage("The channel is not available")


    def getUserInput(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(4000))
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            keyword = kbd.getText()
        return keyword

    def search(self, url):
        keyword = self.getUserInput()

        values = {
            "do": "search",
            "subaction": "search",
            "story": keyword
        }

        headers = {
            "Host": "tivix.co",
            "Origin": "http://tivix.co",
            "Referer": "http://tivix.co/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.3"
        }

        request = urllib2.Request(url, urllib.urlencode(values), headers)
        response = urllib2.urlopen(request).read()

        self.parse(response, filter = keyword.decode('utf-8'))


    def strip(self, string):
        return common.stripTags(string)

    def showErrorMessage(self, msg):
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(10 * 1000)))

plugin = Tivix()
plugin.main()
