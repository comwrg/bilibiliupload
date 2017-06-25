# coding=utf-8
'''
@author: comwrg
@license: MIT
@time : 2017/06/09
@desc : 
'''

import math
import os
import re

import requests

import utils
import time
import base64


class Bilibili:
    def __init__(self, cookie=''):
        # cookie = 'UM_distinctid=15ad6ed506d8a9-0709cb00d6530d-6a11157a-1aeaa0-15ad6ed506e794; fts=1489664561; pgv_pvi=470152192; sid=7x2bt5eo; buvid3=FE847D05-3301-42BD-AC2D-25327D3DF19228064infoc; rpdid=oqqwppklsidoplwowkqpw; LIVE_BUVID=d815f75def06ae324889da90d7f18935; LIVE_BUVID__ckMd5=e04169814ee61cb4; finger=7360d3c2; _ga=GA1.2.3490919.1490526399; LIVE_LOGIN_DATA=187115e74e4856f5d18986a2d8f30abdcb54770f; LIVE_LOGIN_DATA__ckMd5=37b109422e5fab32; purl_token=bilibili_1497149920; DedeUserID=132604873; DedeUserID__ckMd5=e6a58ccc06aec8f8; SESSDATA=4de5769d%2C1497234962%2C20460f14; bili_jct=c8cd121a741e832f91cba99d357f3049; _cnt_pm=0; _cnt_notify=0; _cnt_dyn=0; _cnt_dyn__ckMd5=42c5c8dec5428373; pgv_si=s6399575040; CNZZDATA2724999=cnzz_eid%3D1823204898-1489660091-https%253A%252F%252Fwww.google.com%252F%26ntime%3D1497150146; _dfcaptcha=7b3fe04c01e9621959ec62b94e207bf3'
        self.session = requests.session()
        self.session.headers["cookie"] = cookie
        self.csrf = re.search('bili_jct=(.*?);', cookie).group(1)
        self.mid = re.search('DedeUserID=(.*?);', cookie).group(1)
        self.session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        self.session.headers['Referer'] = 'https://space.bilibili.com/{mid}/#!/'.format(mid=self.mid)
        # session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
        # session.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

    def upload(self,
               filepath,
               source,
               title,
               tid,
               tag,
               desc,
               cover='',
               no_reprint=1,
               copyright=2
               ):
        """
        
        ------WebKitFormBoundaryA1hnRocMNqOz2G9N
        Content-Disposition: form-data; name="file"; filename="1.MP4"
        Content-Type: video/mp4

        ------WebKitFormBoundaryA1hnRocMNqOz2G9N
        Content-Disposition: form-data; name="chunk"

        0
        ------WebKitFormBoundaryA1hnRocMNqOz2G9N
        Content-Disposition: form-data; name="chunks"

        2
        ------WebKitFormBoundaryA1hnRocMNqOz2G9N
        Content-Disposition: form-data; name="filesize"

        10485760
        ------WebKitFormBoundaryA1hnRocMNqOz2G9N
        Content-Disposition: form-data; name="version"

        1.0.1
        ------WebKitFormBoundaryA1hnRocMNqOz2G9N
        Content-Disposition: form-data; name="md5"

        a18c9cd7fe6543794b89e018eea77cd5
        ------WebKitFormBoundaryA1hnRocMNqOz2G9N--
        :type copyright int
        :param copyright: 1 or 2, 1=自制, 2=转载(default)
        :param source:转载地址
        :type no_reprint int
        :param no_reprint: 0=可以转载, 1=禁止转载(default)
        :type tid int
        :param tid: https://member.bilibili.com/x/web/archive/pre
        :param cover:
        :return: 
        """

        r = self.session.get("http://member.bilibili.com/preupload?profile=ugcfr%2Fweb3&mid=26941566&_=1496916151461")
        j = r.json()
        url = j['url']
        url_complete = j['complete']
        url_filename = j['filename']
        self.session.options(url)
        filename = '1.MP4'
        with open(filepath, 'rb') as f:
            # 1M = 1024K = 1024 * 1024B
            CHUNK_SIZE = 10 * 1024 * 1024
            filesize = os.path.getsize(filepath)
            chunks_num = math.ceil(filesize / CHUNK_SIZE)
            chunks_index = 0
            while True:
                chunks_data = f.read(CHUNK_SIZE)
                if not chunks_data:
                    break
                chunks_index += 1
                file = [
                    ('file', (filename, chunks_data, 'video/mp4')),
                    ('chunk', (None, str(chunks_index), None)),
                    ('chunks', (None, str(chunks_num), None)),
                    ('filesize', (None, str(len(chunks_data)), None)),
                    ('version', (None, '1.0.1', None)),
                    ('md5', (None, utils.md5(chunks_data), None))
                ]
                r = self.session.post(url, files=file)
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

        r = self.session.post('https://member.bilibili.com/x/vu/web/add',
                              json={
                                  "copyright" : copyright,
                                  "source"    : source,
                                  "title"     : title,
                                  "tid"       : tid,
                                  "tag"       : tag,
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

    def addVideo(self, cid, aids):
        '''

        :param cid:
        :param aids: type:list, [123, 123, 123]
        :return:
        '''

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

    def up(self, f):
        r = self.session.post(
                url='https://member.bilibili.com/x/vu/web/cover/up',
                data={
                    'cover': b'data:image/jpeg;base64,' + (base64.b64encode(f.read()))
                }
        )
        # print(r.text)
        # {"code":0,"data":{"url":"http://i0.hdslb.com/bfs/archive/67db4a6eae398c309244e74f6e85ae8d813bd7c9.jpg"},"message":"","ttl":1}
        return r.json()['data']['url']


def main():
    pass

if __name__ == '__main__':
    main()
