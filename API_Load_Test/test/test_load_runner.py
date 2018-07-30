
from API_Load_Test.load_runner import LoadRunner
from API_Load_Test.test.api_test import APITest
import os

API_LOAD_TEST_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_LOCUST_FILE = os.path.join(API_LOAD_TEST_PATH, "master_locust.py")
SLAVE_LOCUST_FILE = os.path.join(API_LOAD_TEST_PATH, "api_locust.py")



class TestLoadRunner(APITest):
    """
    These Tests are dependnet on the test_api_locust suit -- especially the test_user_recordigns_ribbon_route tests
    """




    def test_run_single_core_no_web(self):
        self._test_undistributed("User Recordings Ribbon", 1, False)


    def test_run_single_core_web(self):
        self._test_undistributed("User Recordings Ribbon", 1, True)


    def test_run_multi_core_no_web(self):
        self._test_multi_core("User Recordings Ribbon", 1, False)

    def test_run_multi_core_web(self):
        self._test_multi_core("User Recordings Ribbon", 1, True)










