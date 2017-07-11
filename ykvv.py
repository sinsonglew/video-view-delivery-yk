import getopt
import json
import locale
import logging
import os
import platform
import re
import socket
import sys
import time
import uuid
import random
import string
from urllib import request, parse, error

cookies = None
class YKPingback(object):
    def __init__(self, playurl):
        self.vinfo = None
        self.emb = 'AjY3Mzk1Nzc4NgJ2LnlvdWt1LmNvbQIvdl9zaG93L2lkX1hNalk1TlRnek1URTBOQT09Lmh0bWw='
        self.playurl = playurl
        ts = int(time.time() * 1000) - random.randint(100,1000)
        
        self.pingback = dict(
            pc_i = str((ts - random.randint(3,13))) + self.id_generator(3),     # flashvar.ysuid
            pc_u = 0,
            yvft = ts,      # timestamp not generated in player
            seid = str((ts - random.randint(1,3))) + self.id_generator(3),       # '1491752357968dz7', 
            svstp = 70,
            vsidc = 1,
            vstp = 1,
            pvid = str((ts + random.randint(3,13))) + self.id_generator(),
            rvpvid = '',
            ycid = 'dd-3-00-306354-673957786', ######### not sure at present ##########
            rycid = '',
            continuationPlay = 1, #continue play state
            pid = 'null',         #parterId
            videoOwnerId = 11,    #videoInfo.video.userId
            topHdVideo = '',
            viewUserId = '',       #videoInfo.user.uid
            cs = '',               #videoInfo.video.cs
            rnd = int(time.time()),#random number
            frame = 'undefined',
            guid = '',
            timestamp = int(time.time() * 1000),
            showid_v2 = '',                   #videoInfo.show.id
            cna = 'YEJxEVGBt3ICAbRP9c0ffgSV', #flashvar.cna
            oip = '10.10.10.10',              #videoInfo.user.ip
            showid_v3 = '',                   #videoInfo.show.encodeid
            number = 0,                       #59 start to play 60 playing 61 end
            unCookie = 0,                     #flashvar.unCookie
            show_videotype = 0,               #videoInfo.show.video_type
            mtype = 'oth',
            source = 'video',
            stg = 18,                         #videoInfo.show.stage
            playState = 1,
            url = playurl,
            isvip = 0,
            ct = 'd',                         #videoInfo.video.category_letter_id
            Tid = 0,
            pb = 0,
            format = 2,
            Copyright = 0,                   #videoInfo.show.copyright
            ctype = '0401',
            hd = 0,
            sid = 'cf238231e8a1459e7ad23ced1dd18447', #videoInfo.ups.psid
            Type = 0,
            totalsec = 10,      #videoInfo.video.seconds
            winType = 1,
            playComplete = 0,   #play finished state
            fullflag = 0,       #fullscreen state
            paystate = 0,       #videoInfo.show.pay_type transformed
            ikuflag = 'u',
            referUrl = 'null',
            videoid = 1234556,  #videoInfo.video.id
            starttime = 0,
            emb = '', #flashvar.embedid
            langid = 1,
            currentPlayTime = 0
        )


    def id_generator(self, size=6, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(list(chars)) for _ in range(size))
        
    def match1(self, text, *patterns):
        """Scans through a string for substrings matched some patterns (first-subgroups only).
        Args:
            text: A string to be scanned.
            patterns: Arbitrary number of regex patterns.
        Returns:
            When only one pattern is given, returns a string (None if no match found).
            When more than one pattern are given, returns a list of strings ([] if no match found).
        """
        if len(patterns) == 1:
            pattern = patterns[0]
            match = re.search(pattern, text)
            if match:
                return match.group(1)
            else:
                return None
        else:
            ret = []
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    ret.append(match.group(1))
            return ret




    def getVidByUrl(self, url):
        """Extracts video ID from URL.
        """
        return self.match1(url, re.compile(r'youku\.com/v_show/id_([a-zA-Z0-9=]+)'))

    def ungzip(self, data):
        """Decompresses data for Content-Encoding: gzip.
        """
        from io import BytesIO
        import gzip
        buffer = BytesIO(data)
        f = gzip.GzipFile(fileobj=buffer)
        return f.read()

    def undeflate(self, data):
        """Decompresses data for Content-Encoding: deflate.
        (the zlib compression is used.)
        """
        import zlib
        decompressobj = zlib.decompressobj(-zlib.MAX_WBITS)
        return decompressobj.decompress(data)+decompressobj.flush()
    
    def urlopen_with_retry(self, *args, **kwargs):
        for i in range(3):
            try:
                return request.urlopen(*args, **kwargs)
            except socket.timeout:
                logging.debug('request attempt %s timeout' % str(i + 1))

            
    def getContent(self, url, headers={}, decoded=True):
        """Gets the content of a URL via sending a HTTP GET request.
        Args:
            url: A URL.
            headers: Request headers used by the client.
            decoded: Whether decode the response body using UTF-8 or the charset specified in Content-Type.
        Returns:
            The content as a string.
        """

        logging.debug('get_content: %s' % url)

        req = request.Request(url, headers=headers)
        if cookies:
            cookies.add_cookie_header(req)
            req.headers.update(req.unredirected_hdrs)

        response = self.urlopen_with_retry(req)
        data = response.read()

        # Handle HTTP compression for gzip and deflate (zlib)
        content_encoding = response.getheader('Content-Encoding')
        if content_encoding == 'gzip':
            data = self.ungzip(data)
        elif content_encoding == 'deflate':
            data = self.undeflate(data)

        # Decode the response body
        if decoded:
            charset = self.match1(response.getheader('Content-Type'), r'charset=([\w-]+)')
            if charset is not None:
                data = data.decode(charset)
            else:
                data = data.decode('utf-8', 'ignore')

        return data

    def postContent(self, url, headers={}, post_data={}, decoded=True):
        """Post the content of a URL via sending a HTTP POST request.
        Args:
            url: A URL.
            headers: Request headers used by the client.
            decoded: Whether decode the response body using UTF-8 or the charset specified in Content-Type.
        Returns:
            The content as a string.
        """

        logging.debug('post_content: %s \n post_data: %s' % (url, post_data))

        req = request.Request(url, headers=headers)
        if cookies:
            cookies.add_cookie_header(req)
            req.headers.update(req.unredirected_hdrs)
        post_data_enc = bytes(parse.urlencode(post_data), 'utf-8')
        response = self.urlopen_with_retry(req, data=post_data_enc)
        data = response.read()

        # Handle HTTP compression for gzip and deflate (zlib)
        content_encoding = response.getheader('Content-Encoding')
        if content_encoding == 'gzip':
            data = self.ungzip(data)
        elif content_encoding == 'deflate':
            data = self.undeflate(data)

        # Decode the response body
        if decoded:
            charset = self.match1(response.getheader('Content-Type'), r'charset=([\w-]+)')
            if charset is not None:
                data = data.decode(charset)
            else:
                data = data.decode('utf-8')

        print("posted data : ", data)
        return data


    def getVideoInfo(self,vid):
        ups = 'http://ups.youku.com/ups/get.json?vid=%s&ccode=0401&client_ip=&client_ts=&utid=' % vid
        try:
            result = json.loads(self.getContent(
                ups,
                headers={'Referer': 'http://static.youku.com/'}
            ))
            info = result['data']
            assert 'video' in info
        except AssertionError:
            info = None
            logging.error('failed to getContent: %s' % vid)
        return info
    
        
    def startPb(self, num):
        if not self.vinfo:
            vid = self.getVidByUrl(self.pingback['url'])
            self.vinfo = self.getVideoInfo(vid)
        
        self.pingback['number'] = num
        self.pingback['videoid'] = self.vinfo['video']['id']
        self.pingback['videoOwnerId'] = self.vinfo['video']['userid']
        self.pingback['viewUserId'] = self.vinfo['user']['uid']
        self.pingback['cs'] = (self.vinfo['video']['cs']) if ('cs' in self.vinfo['video']) else ''
        if 'show' in self.vinfo:
            self.pingback['showid_v2'] = self.vinfo['show']['id']
            self.pingback['showid_v3'] = self.vinfo['show']['encodeid']
            self.pingback['show_videotype'] = self.vinfo['show']['video_type']
            self.pingback['stg'] = self.vinfo['show']['stage']
            self.pingback['Copyright'] = self.vinfo['show']['copyright']
            
        self.pingback['url'] = self.playurl
        self.pingback['oip'] = self.vinfo['user']['ip']
        self.pingback['ct'] = self.vinfo['video']['category_letter_id']
        self.pingback['totalsec'] = self.vinfo['video']['seconds']
        self.pingback['sid'] = self.vinfo['ups']['psid']
        self.pingback['emb'] = self.emb
        self.pingback['starttime'] = 0
        self.pingback['referUrl'] = 'null'
        self.pingback['guid'] = str(uuid.uuid1())
        self.pingback['currentPlayTime'] = random.randint(0,int(self.vinfo['video']['seconds']/3))
        self.pingback['playComplete'] = 0
        self.sendPb();
        

    def playPb(self, num):
        self.pingback['number'] = num
        self.pingback['playComplete'] = 0
        self.pingback['currentPlayTime'] = self.pingback['currentPlayTime'] + random.randint(0,int(self.vinfo['video']['seconds']/2))
        self.pingback.pop('url', None)
        self.pingback.pop('emb', None)
        self.pingback.pop('starttime', None)
        self.pingback.pop('referUrl', None)
        self.sendPb();

    def endPb(self, num):
        self.pingback['number'] = num
        self.pingback['playComplete'] = 1
        self.pingback['currentPlayTime'] = self.vinfo['video']['seconds'] - random.randint(0,3)
        self.pingback.pop('url', None)
        self.pingback.pop('emb', None)
        self.pingback.pop('starttime', None)
        self.pingback.pop('referUrl', None)
        self.sendPb();


    def sendPb(self):
        vvpbUrl = 'http://yt.mmstat.com/yt/vp.vdoview?{q}'.format(q = parse.urlencode(self.pingback))
        self.postContent(
            vvpbUrl,
            headers={'Referer': 'http://static.youku.com/'}
        )
        print('\n', self.pingback)
        
    def sendvv(self):
        self.startPb(59)
        self.playPb(60)
        self.endPb(61)
        

if __name__ == "__main__":
    x = YKPingback("http://v.youku.com/v_show/id_XMjY5NTgzMTE0NA==.html")
    for i in range(3):
        print('-----%d vv pingback sent \n' % i)
        x.sendvv()
    
    


        
        
        
        
        
        
        
        
    
