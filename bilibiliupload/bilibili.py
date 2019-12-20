# -*- coding: utf-8 -*-

"""
:author: comwrg
:license: MIT
:time: 2017/06/09
"""

import base64
import hashlib
import logging
import math
import os
import re
import requests
import rsa
import time

from io import BufferedReader
from typing import *
from urllib import parse

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class VideoPart:
    def __init__(self, path, title='', desc=''):
        self.path = path
        self.title = title
        self.desc = desc

    def __repr__(self):
        return '<{clazz}, path: {path}, title: {title}, desc: {desc}>'.format(clazz=self.__class__.__name__, path=self.path, title=self.title, desc=self.desc)

class Bilibili:
    def __init__(self, cookie=None):
        self.session = requests.session()
        # debug
        def debug_response(r, *args, **kwargs):
            log.debug(r.text)
        self.session.hooks = {'response': debug_response}
        #
        if cookie:
            self.session.headers["cookie"] = cookie
            self.csrf = re.search('bili_jct=(.*?)(;|$)', cookie).group(1)
            self.mid = re.search('DedeUserID=(.*?)(;|$)', cookie).group(1)
            self.session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
            self.session.headers['Referer'] = 'https://space.bilibili.com/{mid}/#!/'.format(mid=self.mid)
            # session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
            # session.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

    def login(self, user, pwd):
        """

        :param user: username
        :type user: str
        :param pwd: password
        :type pwd: str
        :return: if success return True
                 else raise Exception
        """
        APPKEY    = '4409e2ce8ffd12b8'
        ACTIONKEY = 'appkey'
        BUILD     = 101800
        DEVICE    = 'android'
        MOBI_APP  = 'android'
        PLATFORM  = 'android'
        APPSECRET = '59b43e04ad6965f34319062b478f83dd'

        def md5(s):
            h = hashlib.md5()
            h.update(s.encode('utf-8'))
            return h.hexdigest()

        def sign(s):
            """

            :return: return sign
            """
            return md5(s + APPSECRET)

        def signed_body(body):
            """

            :return: body which be added sign
            """
            if isinstance(body, str):
                return body + '&sign=' + sign(body)
            elif isinstance(body, dict):
                ls = []
                for k, v in body.items():
                    ls.append(k + '=' + v)
                body['sign'] = sign('&'.join(ls))
                return body

        def getkey():
            """

            :return: hash, key
            """
            r = self.session.post(
                    'https://passport.bilibili.com/api/oauth2/getKey',
                    signed_body({'appkey': APPKEY}),
            )
            # {"ts":1544152439,"code":0,"data":{"hash":"99c7573759582e0b","key":"-----BEGIN PUBLIC----- -----END PUBLIC KEY-----\n"}}
            json = r.json()
            data = json['data']
            return data['hash'], data['key']

        def cnn_captcha(img):
            url = "http://47.95.255.188:5000/code"
            data = {"image": img}
            r = requests.post(url, data=data)
            return r.text

        self.session.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        h, k = getkey()
        pwd = base64.b64encode(
                  rsa.encrypt(
                      (h + pwd).encode('utf-8'),
                      rsa.PublicKey.load_pkcs1_openssl_pem(k.encode()),
                  ),
        )
        user = parse.quote_plus(user)
        pwd  = parse.quote_plus(pwd)

        r = self.session.post(
                'https://passport.bilibili.com/api/v2/oauth2/login',
                signed_body('appkey={appkey}&password={password}&username={username}'
                            .format(appkey=APPKEY, username=user, password=pwd)),
        )
        json = r.json()

        if json['code'] == -105:
            # need captcha
            self.session.headers['cookie'] = 'sid=xxxxxxxx'
            r = self.session.get('https://passport.bilibili.com/captcha')
            captcha = cnn_captcha(base64.b64encode(r.content))
            r = self.session.post(
                    'https://passport.bilibili.com/api/v2/oauth2/login',
                    signed_body('actionKey={actionKey}&appkey={appkey}&build={build}&captcha={captcha}&device={device}'
                                '&mobi_app={mobi_app}&password={password}&platform={platform}&username={username}'
                                .format(actionKey=ACTIONKEY,
                                        appkey=APPKEY,
                                        build=BUILD,
                                        captcha=captcha,
                                        device=DEVICE,
                                        mobi_app=MOBI_APP,
                                        password=pwd,
                                        platform=PLATFORM,
                                        username=user)),
            )
            json = r.json()

        if json['code'] != 0:
            raise Exception(r.text)

        cookie = '; '.join(
            '%s=%s' % (item['name'], item['value'])
            for item in json['data']['cookie_info']['cookies']
        )
        self.session.headers["cookie"] = cookie
        self.csrf = re.search('bili_jct=(.*?)(;|$)', cookie).group(1)
        self.mid = re.search('DedeUserID=(.*?)(;|$)', cookie).group(1)
        self.session.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        self.session.headers['Referer'] = 'https://space.bilibili.com/{mid}/#!/'.format(mid=self.mid)

        return True

    def upload(self,
               parts: Union[VideoPart, List[VideoPart]],
               title: str,
               tid: int,
               tag: List[str],
               desc: str,
               source='',
               cover='',
               no_reprint: bool = True,
               dynamic='',
               dtime=None,
               open_elec: bool = True,
               open_subtitle: bool = True,
               max_retry=5,
               ):
        """

        :param parts: e.g. VideoPart('part path', 'part title', 'part desc'), or [VideoPart(...), VideoPart(...)]
        :type parts: Union[VideoPart, List[VideoPart]]
        :param title: video's title
        :type title: str
        :param tid: video type, see: https://member.bilibili.com/x/web/archive/pre
                                  or https://github.com/uupers/BiliSpider/wiki/%E8%A7%86%E9%A2%91%E5%88%86%E5%8C%BA%E5%AF%B9%E5%BA%94%E8%A1%A8
        :type tid: int
        :param tag: video's tag
        :type tag: List[str]
        :param desc: video's description
        :type desc: str 注: 最大长度 250，超过长度B站服务器会报错
        :param dtime: (optional) publish date timestamp (10 digits Unix timestamp e.g. 1551533438)
        :type dtime: int
        :param source: (optional) 转载地址
        :type source: str
        :param cover: (optional) cover's URL, use method *cover_up* to get
        :type cover: str
        :param no_reprint: (optional) Is reprint allowed
        :type no_reprint: bool
        :param dynamic: 粉丝动态
        :type dynamic: str
        :param open_elec: (optional) whether to open charging panel (充电面板)
        :type open_elec: bool
        :param open_subtitle: (optional) Is uploading subtitles allowed
        :type open_subtitle: bool
        :param max_retry: (optional) max retry times per chunk
        :type max_retry: int
        """

        if len(title) > 80:
            raise Exception("标题长度超过80字")
        if len(desc) > 250:
            raise Exception("视频描述超过250字")
        if len(source) > 200:
            raise Exception("转载地址长度超过200字")

        self.session.headers['Content-Type'] = 'application/json; charset=utf-8'
        if not isinstance(parts, list):
            parts = [parts]

        videos = []
        for part in parts:
            filepath = part.path
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            r = self.session.get('https://member.bilibili.com/preupload?'
                                 'os=upos&upcdn=ws&name={name}&size={size}&r=upos&profile=ugcupos%2Fyb&ssl=0'
                                 .format(name=parse.quote_plus(filename), size=filesize))
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

                    def upload_chunk():
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
                        return r

                    def retry_upload_chunk():
                        """return :class:`Response` if upload success, else return None."""
                        for i in range(max_retry):
                            r = upload_chunk()
                            if r.status_code == 200:
                                return r
                            log.info(r.text)
                            log.info('{}/{} retry stage {}/{}'.format(chunks_index, chunks_num, i, max_retry))
                            log.info('sleep %ds', 5 * i)
                            time.sleep(5 * i)
                        return None

                    r = retry_upload_chunk()
                    if r:
                        log.info('upload part {}/{}'.format(chunks_index, chunks_num))
                    else:
                        raise Exception('upload reach max retry times at part {}/{}'.format(chunks_index, chunks_num))

                # NOT DELETE! Refer to https://github.com/comwrg/bilibiliupload/issues/15#issuecomment-424379769
                self.session.post('https:{endpoint}/{upos_uri}?'
                                  'output=json&name={name}&profile=ugcupos%2Fyb&uploadId={upload_id}&biz_id={biz_id}'
                                  .format(endpoint=endpoint,
                                          upos_uri=upos_uri.replace('upos://', ''),
                                          name=filename,
                                          upload_id=upload_id,
                                          biz_id=biz_id,
                                  ),
                                  {"parts": [{"partNumber": i, "eTag": "etag"} for i in range(1, chunks_num+1)]},
                )

            videos.append({'filename': upos_uri.replace('upos://ugc/', '').split('.')[0],
                           'title'   : part.title,
                           'desc'    : part.desc})

        # if source is empty, copyright=1, else copyright=2
        copyright = 2 if source else 1
        def add():
            r = self.session.post('https://member.bilibili.com/x/vu/web/add?csrf=' + self.csrf,
                                  json={
                                      "copyright" : copyright,
                                      "source"    : source,
                                      "title"     : title,
                                      "tid"       : tid,
                                      "tag"       : ','.join(tag),
                                      "no_reprint": int(no_reprint),
                                      "desc"      : desc,
                                      "cover"     : cover,
                                      "mission_id": 0,
                                      "order_id"  : 0,
                                      "videos"    : videos,
                                      "dtime"     : dtime,
                                      "open_elec" : int(open_elec),
                                      "dynamic"   : dynamic,
                                      "subtitle"  : {
                                          "lan" : "",
                                          "open": int(open_subtitle),
                                      },
                                  },
            )
            return r

        def retry_add():
            for i in range(max_retry):
                r = add()
                json = r.json()
                code = json['code']
                if code == 0:
                    return r
                # {"code":20001,"message":"投稿服务异常","ttl":1}
                if code in (20001, ):
                    log.info('retry add video {}/{}, {}'.format(i, max_retry, r.text))
                else:
                    raise Exception('Fail to add video, {}'.format(r.text))
                log.info('sleep %ds', 5 * i)
                time.sleep(5 * i)
            raise Exception('Add video reach max retry times.')

        r = retry_add()
        return r.json()

    def addChannel(self, name, intro=''):
        """

        :param name: channel's name
        :type name: str
        :param intro: channel's introduction
        :type intro: str
        """
        r = self.session.post(
                url='https://api.bilibili.com/x/space/channel/add',
                data={
                    'name' : name,
                    'intro': intro,
                    'jsonp' : 'jsonp',
                    'csrf' : self.csrf,
                },
                # name=123&intro=123&aids=&csrf=565d7ed17cef2cc8ad054210c4e64324&_=1497077610768

        )
        # return
        # {"status":true,"data":{"cid":"15812"}}

    def channel_addVideo(self, cid, aids):
        """

        :param cid: channel's id
        :type cid: int
        :param aids: videos' id
        :type aids: list<int>
        """

        r = self.session.post(
                url='https://api.bilibili.com/x/space/channel/video/add',
                data={
                    'aids': '%2C'.join(aids),
                    'cid' : cid,
                    'csrf': self.csrf,
                },
                # aids=9953555%2C9872953&cid=15814&csrf=565d7ed17cef2cc8ad054210c4e64324&_=1497079332679
        )

    def cover_up(self, img: Union[str, BufferedReader]):
        """

        :param img: img path or stream
        :return: img URL
        """

        if isinstance(img, str):
            f = open(img, 'rb')
        else:
            f = img
        self.session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        r = self.session.post(
                url='https://member.bilibili.com/x/vu/web/cover/up',
                data={
                    'cover': b'data:image/jpeg;base64,' + (base64.b64encode(f.read())),
                    'csrf': self.csrf,
                },
        )
        # {"code":0,"data":{"url":"http://i0.hdslb.com/bfs/archive/67db4a6eae398c309244e74f6e85ae8d813bd7c9.jpg"},"message":"","ttl":1}
        return r.json()['data']['url']

