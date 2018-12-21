from unittest import TestCase
from app.Utils import utils


class TestUtils(TestCase):


    def test_get_performance_test_dir(self):
        self.assertEqual(utils.get_performance_test_dir()[-16:], "Performance_Test")

    def test_get_entrance_path(self):
        self.assertEqual(utils.get_entrance_path(), utils.get_performance_test_dir() + "/main.py")

    def test_start_hosts(self):
        utils.start_hosts(["b-gp2-lgen-8.imovetv.com"], "NOT_A_PROG")
