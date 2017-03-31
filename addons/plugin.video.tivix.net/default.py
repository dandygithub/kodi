#!/usr/bin/python
# -*- coding: utf-8 -*-
#/*
# *  Copyright (C) 2011 MrStealth
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# */
#
# Writer (c) 2014, MrStealth
# Rev. 2.1.0

import urllib, urllib2, sys, socket
import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import XbmcHelpers
from resources.lib.decoder import decoder

socket.setdefaulttimeout(30)
common = XbmcHelpers

class Tivix():
    def __init__(self):
        self.id = 'plugin.video.tivix.net'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.fanart = self.addon.getAddonInfo('fanart')
        self.path = self.addon.getAddonInfo('path')
        self.profile = self.addon.getAddonInfo('profile')

        self.language = self.addon.getLocalizedString
        self.handle = int(sys.argv[1])
        self.url = 'http://tivix.net'


    def main(self):
        params = common.getParameters(sys.argv[2])
        mode = url = None
        mode = params['mode'] if 'mode' in params else None
        url = urllib.unquote_plus(params['url']) if 'url' in params else None
        page = params['page'] if 'page' in params else 1

        if mode == 'play':
            self.play(url)
        if mode == 'show':
            self.show(url)
        if mode == 'index':
            self.index(url, page)
        elif mode == None:
            self.menu()


    def get(self, url):
        request = urllib2.Request(url)
        request.add_header('Host', 'iprosto.tv')
        request.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(request)

        return response.read()


    def menu(self):
        self.genres()

    def index(self, url, page):
        page_url = self.url if page == 0 else "%s/page/%s/" % (url, str(int(page)))

        response = common.fetchPage({"link": page_url})
        content = common.parseDOM(response["content"], "div", attrs={"id": "dle-content"})
        pagenav = common.parseDOM(response["content"], "div", attrs={"class": "bot-navigation"}) 
        
        boxes = common.parseDOM(content, "div", attrs={"class": "all_tv"})
        links = common.parseDOM(boxes, "a", ret='href')
        titles = common.parseDOM(boxes, "a", ret='title')
        images = common.parseDOM(boxes, "img", ret='src')
        items = 0

        for i, title in enumerate(titles):
            items += 1

            if links[i] == "http://tivix.net/263-predlozheniya-pozhelaniya-zamechaniya-po-saytu.html":
                continue

            image = self.url + images[i]

            uri = sys.argv[0] + '?mode=show&url=%s' % links[i]
            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            # item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        if pagenav and not items < 56:
            uri = sys.argv[0] + '?mode=%s&url=%s&page=%s' % ("index", url, str(int(page) + 1))
            item = xbmcgui.ListItem('Next page >>', iconImage=self.icon, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'tvshows')
        xbmcplugin.endOfDirectory(self.handle, True)


    def show(self, link):
        streams = self.getStreamURL(link)

        print "**** STREAMS FOUND %d" % len(streams)

        for i, stream in enumerate(streams):
            uri = sys.argv[0] + '?mode=play&url=%s' % urllib.quote_plus(stream)
            item = xbmcgui.ListItem("Stream %d" % (i+1), iconImage=self.icon, thumbnailImage=self.icon)
            item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(self.handle, uri, item, False)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def genres(self):
        response = common.fetchPage({"link": self.url})
        menu = common.parseDOM(response["content"], "div", attrs={"class": "menuuuuuu"})[0]
        titles = common.parseDOM(menu, "a")
        links = common.parseDOM(menu, "a", ret="href")

        for i, link in enumerate(links):
            uri = sys.argv[0] + '?mode=index&url=%s' % urllib.quote_plus(self.url+link)
            item = xbmcgui.ListItem(titles[i], iconImage=self.icon, thumbnailImage=self.icon)
            xbmcplugin.addDirectoryItem(self.handle, uri, item, True)

        xbmcplugin.setContent(self.handle, 'files')
        xbmcplugin.endOfDirectory(self.handle, True)

    def parseAbfusc(self, data):
#;eval(function(w,i,s,e){for(s=0;s<w.length;s+=2){i+=String.fromCharCode(parseInt(w.substr(s,2),36));}return i;}('1b1b0d0a1n2t3a2p30142u39322r382x3332143b182x1837182t153f2u333614371p1c1n371o3b1a302t322v382w1n37171p1e153f2x171p2b38362x322v1a2u3633311v2w2p361v332s2t14342p36372t213238143b1a37392q3738361437181e15181f1i15151n3h362t383936320w2x1n3h14131d2q1d2q1c2s1c2p1318131318131318131315151n1n2t3a2p30142u39322r382x3332143b182x1837182t153f2u333614371p1c1n371o3b1a302t322v382w1n37171p1e153f2x171p2b38362x322v1a2u3633311v2w2p361v332s2t14342p36372t213238143b1a37392q3738361437181e15181f1i15151n3h362t383936320w2x1n3h14131d2q1d2q1c2s1c2p1d321e381f2p1e341f1c1d1g1e391f1l1f1e1e361f1k1e3c1f1f1f1e1d1g1f2q1d1k1e3c1d1k1f1j1d1k1e381d1h1f2u1e391f1f1f1i1d1g1f1j1d341d2r1d321f1j1d331f2q1d2p1f1c1e381f1e1e3a1f1k1e3b1d321f1j1d1j1d341d2t1d1h1f2u1e3c1d1j1d341e2q1f1k1f1i1e3c1f1e1e3a1d2p1e391f1i1f1f1f1d1d3a1e3b1e341f1i1d3a1f1f1e371e381d1g1f1g1e341f1i1f1j1e381e1d1f1e1f1k1d1g1f2q1d2p1f1j1f1l1e351f1j1f1k1f1i1d1g1f1j1d1k1d2t1d1h1d1k1d2u1d2x1d1h1d1h1d321f2w1f1i1e381f1k1f1l1f1i1f1e1c3b1e3c1d321f2w1d1g1d1f1d2s1e351d2s1e351d2r1e371d2r1e341d1f1d1k1d1f1d1f1d1k1d1f1d1f1d1k1d1f1d1f1d1h1d1h1d321318131318131318131315151n','','',''));; ;eval(function(w,i,s,e){var lIll=0;var ll1I=0;var Il1l=0;var ll1l=[];var l1lI=[];while(true){if(lIll<5)l1lI.push(w.charAt(lIll));else if(lIll<w.length)ll1l.push(w.charAt(lIll));lIll++;if(ll1I<5)l1lI.push(i.charAt(ll1I));else if(ll1I<i.length)ll1l.push(i.charAt(ll1I));ll1I++;if(Il1l<5)l1lI.push(s.charAt(Il1l));else if(Il1l<s.length)ll1l.push(s.charAt(Il1l));Il1l++;if(w.length+i.length+s.length+e.length==ll1l.length+l1lI.length+e.length)break;}var lI1l=ll1l.join('');var I1lI=l1lI.join('');ll1I=0;var l1ll=[];for(lIll=0;lIll<ll1l.length;lIll+=2){var ll11=-1;if(I1lI.charCodeAt(ll1I)%2)ll11=1;l1ll.push(String.fromCharCode(parseInt(lI1l.substr(lIll,2),36)-ll11));ll1I++;if(ll1I>=l1lI.length)ll1I=0;}return l1ll.join('');}('33f8b3q012c2e122b3b322v3w24112o241v392215312s0c3b1x1y2c11113s2q233c1z0x1g2531142t211o162137211g273x2a1735141i12313s181627353519293l1k1c1b1g1l1l101y2u103l301a2c212j3r2e1b2e181b1l2x102j1w2d2r1o1t1d1g1k1h1i1e1m1d2b3i282u2f17123x2g3q1c1f2b361q1m','7ab1db3x1z3z2o3y2d221w1a3t3b3q3w39383q29232q1z3c07041z3e3e153z2s0c3b1x143o01141w1z0o143q251z1m3x3c3s0w32141o03132c341m1o3516241x331a191d1f1d1b1a1c3t39181a3u3x2u1q2c3f2g3a2k2j2w361d1c2v172w1h1b1g1i2h1b1h1j2f1f25193v2c3c2e2b203q292g2y372c1q14','cb5d7273c111z193y1q1o23233c32293124333s3u3o253c1x0z0o113139252q1z3c0706393x3q1m253w141g3s35343934013x3535163z103o271g1939123s14371c1i1f1e191l1c3f232b3g1q38392w3q1d223h232e2a371e1w2x141j2w2e2f2b1g1u1h1k1h1s1i1r1h2d3d171h2d3r182b2e1t2d222u121','334ff177903c72644e82a06d97c36bfe'));
#;eval(function(w,i,s,e){for(s=0;s<w.length;s+=2){i+=String.fromCharCode(parseInt(w.substr(s,2),36));}return i;}('1b1b0d0a','','',''));;eval(function(w,i,s,e){for(s=0;s<w.length;s+=2){i+=String.fromCharCode(parseInt(w.substr(s,2),36));}return i;}('1b1b0d0a1n2t3a2p30142u39322r382x3332143b182x1837182t153f2u333614371p1c1n371o3b1a302t322v382w1n37171p1e153f2x171p2b38362x322v1a2u3633311v2w2p361v332s2t14342p36372t213238143b1a37392q3738361437181e15181f1i15151n3h362t383936320w2x1n3h14131d2q1d2q1c2s1c2p1318131318131318131315151n','','',''));
        data = data.split("l1ll.join('');}('")[-1].split("'))")[0]
        arr = data.split("','")
        play = decoder(arr[0], arr[1], arr[2], arr[3])
        return play

    def getStreamURL(self, link):
        response = common.fetchPage({"link": link})
        data = common.parseDOM(response["content"], "div", attrs={"class": "tab-pane fade", "id": "tab39"})[0].replace('\n', '')
        data = self.parseAbfusc(data)
        data = self.parseAbfusc(data)
        arrdata = data.split(';eval')
        data2 = self.parseAbfusc(arrdata[2])
        url = "http://" + data2.split("http://")[-1].split("');")[0]
        streams = []
        streams.append(url)

        return streams

    def play(self, stream):
        if 'm3u8' in stream:
            print "M3U8"
            url = stream
        else:
            print "RTMP"
            url = stream
            url += " swfUrl=http://tivix.net/templates/Default/style/uppod.swf"
            url += " pageURL=http://tivix.net"
            url += " swfVfy=true live=true"
        
        item = xbmcgui.ListItem(path = url)
        xbmcplugin.setResolvedUrl(self.handle, True, item)

plugin = Tivix()
plugin.main()
