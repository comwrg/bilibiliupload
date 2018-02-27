import unittest
from bilibili import Bilibili

USERNAME = ''
PASSWORD = ''


class TestBilibili(unittest.TestCase):
    def test_login(self):
        self.b = Bilibili()
        r = self.b.login(USERNAME, PASSWORD)
        self.assertTrue(r)

    def test_upload(self):
        pass


if __name__ == '__main__':
    # reference: https://stackoverflow.com/questions/4005695/changing-order-of-unit-tests-in-python
    # test by line number
    ln = lambda f: getattr(TestBilibili, f).__code__.co_firstlineno
    ln_cmp = lambda _, a, b: ln(a) - ln(b)
    unittest.TestLoader.sortTestMethodsUsing = ln_cmp
    unittest.main()
