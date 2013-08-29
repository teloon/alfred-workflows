#!/usr/bin/env python
#-*- coding:utf-8 -*-

import json
import sys
import urllib
import urllib2
from Feedback import Feedback

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
}

def query(query="love the way you lie"):
    q_url = 'http://www.xiami.com/app/nineteen/search/key/%s/page/1' % query
    req = urllib2.Request(q_url, headers=HEADERS)
    html = urllib2.urlopen(req).read()

    response = json.loads(html)
    results = response['results']
    fb = Feedback()
    for rcd in results:
        name = urllib.unquote_plus(rcd['song_name']).encode("latin-1").decode("utf-8")
        album = urllib.unquote_plus(rcd['album_name']).encode("latin-1").decode("utf-8")
        artist = urllib.unquote_plus(rcd['artist_name']).encode("latin-1").decode("utf-8")
        song_id = urllib.unquote_plus(rcd['song_id']).encode("latin-1").decode("utf-8")
        fb.add_item("%s - %s" % (artist, name),
                    subtitle=u"歌手:%s 专辑:《%s》" % (artist, album),
                    uid=song_id,
                    arg='http://www.xiami.com/song/' + song_id)
    print fb

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query(sys.argv[1])
