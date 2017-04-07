import sys
import urllib
import urllib2
from urlparse import parse_qs
from urllib2 import URLError

class YoutubeModuleException(Exception):
    pass

class YoutubeModule(object):
    def get_video_info(self, video_url):
        print "*** get_video_info: %s" % video_url
        request_url = 'http://www.youtube.com/get_video_info?video_id='

        if 'http://www.youtube.com/watch?v' in video_url:
            params = video_url.split('?')[-1]
            request_url += parse_qs(params)['v'][0]
        else :
            sys.exit('Error : Invalid Youtube URL Passing %s' % video_url)

        print request_url

        request = urllib2.Request(request_url)

        try:
            self.video_info = parse_qs(urllib2.urlopen(request).read())
            # print "**** Video info"
            # print self.video_info
            return True
        except URLError :
            sys.exit('Error : Invalid Youtube URL Passing %s' % video_url)
            return False

    def get_video_title(self):
        return self.video_info['title'][0].decode('utf-8')

    def video_file_urls(self):
        if 'fail' in self.video_info['status']:
            raise YoutubeModuleException(self.video_info['reason'][0])
        else:
            url_encoded_fmt_stream_map = self.video_info['url_encoded_fmt_stream_map'][0].split(',')
            entrys = [parse_qs(entry) for entry in url_encoded_fmt_stream_map]
            url_maps = [dict(url=entry['url'][0]+'&signature='+entry['sig'][0], type=entry['type']) for entry in entrys]

            return url_maps

    def get_youtube_url(self, url, hd_enabled=False):
        response = self.get_video_info(url)

        fmt = {
            '46': '1920x1080/99/0/0',
            '37': '1920x1080/9/0/115',
            '45': '1280x720/99/0/0',
            '22': '1280x720/9/0/115',
            '44': '854x480/99/0/0',
            '35': '854x480/9/0/115',
            '43': '640x360/99/0/0',
            '34': '640x360/9/0/115',
            '18': '640x360/9/0/115',
        }

        hd = ['45', '22'] # disable FullHD => [46, 37]
        sd = ['44', '35', '43', '34', '16']

        video_url_map = self.video_file_urls()
        video_title = self.get_video_title()

        print "*** HD enabled %s" % hd_enabled
        #print type(hd_enabled)

        if video_url_map:
            # print "======= TITLE: %s" % video_title
            for i, video in enumerate(video_url_map):
                itag = video['url'].split('itag=')[-1].split('&')[0]

                if (hd_enabled and itag in hd):
                    print "HD - %s - ITAG %s (%s)" % (fmt[itag], itag, video['type'])
                    return  video['url']
                elif  (not hd_enabled and itag in sd):
                    print "SD - %s - ITAG %s (%s)" % (fmt[itag], itag, video['type'])
                    return video['url']

        return video_url_map[3]['url']




# url = "http://www.youtube.com/watch?v=ubAKkH9im3I" #barboskiny
# url = 'http://www.youtube.com/watch?v=Gc7lqC0VI6M' #tishka
# url ="http://www.youtube.com/watch?v=tgqXlApMxvw" #fiksiki
# print YoutubeModule().get_youtube_url(url)

# 1) ['video/mp4; codecs="avc1.64001F, mp4a.40.2"'] ==> itag=37
# 2) ['video/webm; codecs="vp8.0, vorbis"'] ==> itag=45
# 3) ['video/mp4; codecs="avc1.64001F, mp4a.40.2"'] ==> itag=22
# 4) ['video/webm; codecs="vp8.0, vorbis"'] ==> itag=44
# 5) ['video/x-flv'] ==> itag=35

# Youtube FMT codes
# 'fmt_list': [
#     46/1920x1080/99/0/0,
#     37/1920x1080/9/0/115,
#     45/1280x720/99/0/0,
#     22/1280x720/9/0/115,
#     44/854x480/99/0/0,     => VORBIS
#     35/854x480/9/0/115,   => FLV
#     43/640x360/99/0/0,
#     34/640x360/9/0/115,
#     18/640x360/9/0/115,
#     5/320x240/7/0/0,
#     36/320x240/99/1/0,
#     17/176x144/99/1/0
# ]
