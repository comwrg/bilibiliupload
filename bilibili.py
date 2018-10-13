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


class VideoPart:
    def __init__(self, path, title='', desc=''):
        self.path = path
        self.title = title
        self.desc = desc

class Bilibili:
    def __init__(self, cookie=None):
        self.session = requests.session()
        if cookie:
            self.session.headers["cookie"] = cookie
            self.csrf = re.search('bili_jct=(.*?);', cookie).group(1)
            self.mid = re.search('DedeUserID=(.*?);', cookie).group(1)
            self.session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
            self.session.headers['Referer'] = 'https://space.bilibili.com/{mid}/#!/'.format(mid=self.mid)
            # session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
            # session.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

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
               parts,
               title,
               tid,
               tag,
               desc,
               source='',
               cover='',
               no_reprint=1,
               ):
        """

        :param parts: e.g. VideoPart('part title', 'part title', 'part desc'), or [VideoPart(...), VideoPart(...)]
        :type parts: VideoPart or list<VideoPart>
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

        if not isinstance(parts, list):
            parts = [parts]

        videos = []
        for part in parts:
            filepath = part.path
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            r = self.session.get('https://member.bilibili.com/preupload?'
                                 'os=upos&upcdn=ws&name={name}&size={size}&r=upos&profile=ugcupos%2Fyb&ssl=0'
                                 .format(name=filename, size=filesize))
            """return example
            {
                "upos_uri": "upos://ugc/i181012ws18x52mti3gg0h33chn3tyhp.mp4",
                "biz_id": 58993125,
                "endpoint": "//upos-hz-upcdnws.acgvideo.com",
                "endpoints": [
                    "//upos-hz-upcdnws.acgvideo.com",
                    "//upos-hz-upcdntx.acgvideo.com"
                ],
                "chunk_retry_delay": 3,
                "chunk_retry": 200,
                "chunk_size": 4194304,
                "threads": 2,
                "timeout": 900,
                "auth": "os=upos&cdn=upcdnws&uid=&net_state=4&device=&build=&os_version=&ak=×tamp=&sign=",
                "OK": 1
            } 
            """
            json = r.json()
            upos_uri = json['upos_uri']
            endpoint = json['endpoint']
            auth = json['auth']
            biz_id = json['biz_id']
            chunk_size = json['chunk_size']
            self.session.headers['X-Upos-Auth'] = auth  # add auth header
            r = self.session.post('https:{}/{}?uploads&output=json'.format(endpoint, upos_uri.replace('upos://', '')))
            # {"upload_id":"72eb747b9650b8c7995fdb0efbdc2bb6","key":"\/i181012ws2wg1tb7tjzswk2voxrwlk1u.mp4","OK":1,"bucket":"ugc"}
            json = r.json()
            upload_id = json['upload_id']

            with open(filepath, 'rb') as f:
                chunks_num = math.ceil(filesize / chunk_size)
                chunks_index = -1
                while True:
                    chunks_data = f.read(chunk_size)
                    if not chunks_data:
                        break
                    chunks_index += 1  # start with 0
                    r = self.session.put('https:{endpoint}/{upos_uri}?'
                                         'partNumber={part_number}&uploadId={upload_id}&chunk={chunk}&chunks={chunks}&size={size}&start={start}&end={end}&total={total}'
                                         .format(endpoint=endpoint,
                                                 upos_uri=upos_uri.replace('upos://', ''),
                                                 part_number=chunks_index+1,  # starts with 1
                                                 upload_id=upload_id,
                                                 chunk=chunks_index,
                                                 chunks=chunks_num,
                                                 size=len(chunks_data),
                                                 start=chunks_index * chunk_size,
                                                 end=chunks_index * chunk_size + len(chunks_data),
                                                 total=filesize,
                                                 ),
                                         chunks_data,
                                         )
                    print('{}/{}'.format(chunks_index, chunks_num), r.text)

            videos.append({'filename': upos_uri.replace('upos://ugc/', '').split('.')[0],
                           'title'   : part.title,
                           'desc'    : part.desc})

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
                                  "videos"    : videos}
                              )
        print(r.text)

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
