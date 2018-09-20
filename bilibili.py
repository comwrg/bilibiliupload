# coding=utf-8
"""
:author: comwrg
:license: MIT
:time: 2017/06/09
"""

import os
import re
import math
import utils
import base64
import requests


class Bilibili:
    def __init__(self):
        self.session = requests.session()

    def login(self, user, pwd):
        """
        .. warning::
           | THE API IS NOT OFFICIAL API
           | DETAILS: https://api.kaaass.net/biliapi/docs/

        :param user: username
        :type user: str
        :param pwd: password
        :type pwd: str
        :return: if success return True
                 else return msg json
        """
        r = requests.post(
                url='https://api.kaaass.net/biliapi/user/login',
                data={
                    'user'  : user,
                    'passwd': pwd
                },
                headers={
                    'x-requested-with': 'XMLHttpRequest'
                }

        )
        # {"ts":1498361700,"status":"OK","mid":132604873,"access_key":"fb6c52162481d92a20875aca101ebe92","expires":1500953701}
        # print(r.text)
        if r.json()['status'] != 'OK':
            return r.json()

        access_key = r.json()['access_key']
        r = requests.get(
                url='https://api.kaaass.net/biliapi/user/sso?access_key=' + access_key,
                headers={
                    'x-requested-with': 'XMLHttpRequest'
                }
        )
        # {"ts":1498361701,"status":"OK","cookie":"sid=4jj9426i; DedeUserID=132604873; DedeUserID__ckMd5=e6a58ccc06aec8f8; SESSDATA=4de5769d%2C1498404903%2Cd86e4dea; bili_jct=5114b3630514ab72df2cb2e7e6fcd2eb"}
        # print(r.text)

        if r.json()['status'] == 'OK':
            cookie = r.json()['cookie']
            self.session.headers["cookie"] = cookie
            self.csrf = re.search('bili_jct=(.*?);', cookie + ';').group(1)
            self.mid = re.search('DedeUserID=(.*?);', cookie + ';').group(1)
            self.session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
            self.session.headers['Referer'] = 'https://space.bilibili.com/{mid}/#!/'.format(mid=self.mid)
            # session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
            # session.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            return True
        else:
            return r.json()

    def upload(self,
               filepath,
               title,
               tid,
               tag,
               desc,
               source='',
               cover='',
               no_reprint=1,
               ):
        """

        :param filepath: file path
        :type filepath: str
        :param title: video's title
        :type title: str
        :param tid: video type, see: https://member.bilibili.com/x/web/archive/pre
        :type tid: int
        :param tag: video's tag
        :type tag: list<str>
        :param desc: video's description
        :type desc: str
        :param source: (optional) 转载地址
        :type source: str
        :param cover: (optional) cover's URL, use method *cover_up* to get
        :type cover: str
        :param no_reprint: (optional) 0=可以转载, 1=禁止转载(default)
        :type no_reprint: int
        """

        r = self.session.get("http://member.bilibili.com/preupload?profile=ugcfr%2Fweb3&mid=26941566&_=1496916151461")
        j = r.json()
        url = j['url']
        url_complete = j['complete']
        url_filename = j['filename']
        self.session.options(url)
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            # 1M = 1024K = 1024 * 1024B
            CHUNK_SIZE = 7 * 1024 * 1024
            filesize = os.path.getsize(filepath)
            chunks_num = math.ceil(filesize / CHUNK_SIZE)
            chunks_index = 0
            while True:
                chunks_data = f.read(CHUNK_SIZE)
                if not chunks_data:
                    break
                chunks_index += 1
                file = [
                    ('file'    , (filename, chunks_data            , 'video/mp4')),
                    ('chunk'   , (None    , str(chunks_index)      , None       )),
                    ('chunks'  , (None    , str(chunks_num)        , None       )),
                    ('filesize', (None    , str(len(chunks_data))  , None       )),
                    ('version' , (None    , '1.0.1'                , None       )),
                    ('md5'     , (None    ,  utils.md5(chunks_data), None       )),
                ]
                r = self.session.post(url, files=file)
                if re.search('504', r.text):
                    chunks_index = 0
                    f.seek(0, 0)
                print(r.text, chunks_num, chunks_index)

        r = self.session.post(url_complete,
                              data={
                                  'name'    : filename,
                                  'chunks'  : chunks_num,
                                  'filesize': filesize,
                                  'csrf'    : self.csrf
                              },
                              headers={
                                  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                              })
        print(r.text)

        # if source is empty, copyright=1, else copyright=2
        copyright = 2 if source else 1
        r = self.session.post('https://member.bilibili.com/x/vu/web/add?csrf=' + self.csrf,
                              json={
                                  "copyright" : copyright,
                                  "source"    : source,
                                  "title"     : title,
                                  "tid"       : tid,
                                  "tag"       : ','.join(tag),
                                  "no_reprint": no_reprint,
                                  "desc"      : desc,
                                  "cover"     : cover,
                                  "mission_id": 0,
                                  "order_id"  : 0,
                                  "videos"    : [{
                                      "desc"    : "",
                                      "filename": url_filename,
                                      "title"   : ""
                                  }]}
                              )
        print(r.content)

    def addChannel(self, name, intro=''):
        """

        :param name: channel's name
        :type name: str
        :param intro: channel's introduction
        :type intro: str
        """
        r = self.session.post(
                url='https://space.bilibili.com/ajax/channel/addChannel',
                data={
                    'name' : name,
                    'intro': intro,
                    'aids' : '',
                    'csrf' : self.csrf,
                },
                # name=123&intro=123&aids=&csrf=565d7ed17cef2cc8ad054210c4e64324&_=1497077610768

        )
        # return
        # {"status":true,"data":{"cid":"15812"}}
        print(r.json())

    def channel_addVideo(self, cid, aids):
        """

        :param cid: channel's id
        :type cid: int
        :param aids: videos' id
        :type aids: list<int>
        """

        r = self.session.post(
                url='https://space.bilibili.com/ajax/channel/addVideo',
                data={
                    'aids': '%2C'.join(aids),
                    'cid' : cid,
                    'csrf': self.csrf
                }
                # aids=9953555%2C9872953&cid=15814&csrf=565d7ed17cef2cc8ad054210c4e64324&_=1497079332679
        )
        print(r.json())

    def cover_up(self, img):
        """

        :param img: img path or stream
        :type img: str or BufferedReader
        :return: img URL
        """

        if isinstance(img, str):
            f = open(img, 'rb')
        else:
            f = img
        r = self.session.post(
                url='https://member.bilibili.com/x/vu/web/cover/up',
                data={
                    'cover': b'data:image/jpeg;base64,' + (base64.b64encode(f.read())),
                    'csrf': self.csrf,
                }
        )
        # print(r.text)
        # {"code":0,"data":{"url":"http://i0.hdslb.com/bfs/archive/67db4a6eae398c309244e74f6e85ae8d813bd7c9.jpg"},"message":"","ttl":1}
        return r.json()['data']['url']


def main():
    pass


if __name__ == '__main__':
    main()
