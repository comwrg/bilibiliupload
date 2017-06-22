# coding=utf-8
'''
@author: comwrg
@license: MIT
@time : 2017/06/10 08:53
@desc : 
'''
import hashlib


def md5(f):
    hash_md5 = hashlib.md5()
    hash_md5.update(f)
    return hash_md5.hexdigest()
