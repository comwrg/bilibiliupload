import os
import re
import random
import unittest
from bilibili import *

USERNAME = ''
PASSWORD = ''

b = Bilibili()

class TestBilibili(unittest.TestCase):
    def test_login(self):
        r = b.login(USERNAME, PASSWORD)
        self.assertTrue(r)

    def test_upload(self):
        VIDEOS_PATTERN = '.+\.[mp4|flv|avi|wmv|mov|webm|mpeg4|ts|mpg|rm|rmvb|mkv]'
        videos = [f for f in os.listdir('bin') if re.match(VIDEOS_PATTERN, f, re.I)]
        for f in videos:
            filepath = os.path.abspath('./bin/' + f)
            title = str(random.randint(1, 10000)) + os.path.basename(filepath)
            tid = 65
            tag = ['test', '测试']
            desc = 'desc, 描述'
            b.upload(VideoPart(filepath), title, tid, tag, desc)



if __name__ == '__main__':
    # reference: https://stackoverflow.com/questions/4005695/changing-order-of-unit-tests-in-python
    # test by line number
    ln = lambda f: getattr(TestBilibili, f).__code__.co_firstlineno
    ln_cmp = lambda _, a, b: ln(a) - ln(b)
    unittest.TestLoader.sortTestMethodsUsing = ln_cmp
    unittest.main()
