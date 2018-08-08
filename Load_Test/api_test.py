from unittest import TestCase
from Load_Test import Config, RequestPoolFactory, LoadRunner
import os
import pandas
import time


class APITest(TestCase):
    LOAD_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
    TEST_DIR = os.path.join(LOAD_TEST_DIR, "test/")
    test_stats_folder = os.path.join(TEST_DIR, "test_stats/")
    SLAVE_LOCUST_FILE = os.path.join(LOAD_TEST_DIR, "api_locust.py")
    MASTER_LOCUST_FILE = os.path.join(LOAD_TEST_DIR, "master_locust.py")

    def setUp(self):
        self.expected_routes = {"User Recordings Ribbon", "User Franchise Ribbon", "User Recspace Information",
                                "Update User Settings",
                                "Create Recordings", "Protect Recordings", "Mark Watched", "Delete Recordings",
                                "Create Rules", "Update Rules",
                                "Delete Rules", "List Rules"}
        self.expected_api_env = {"DEV1", "DEV2", "DEV3", "QA", "BETA", "BETA2"}
        self.config = Config(debug=False)
        self.PoolFactory = RequestPoolFactory(self.config, envs={"DEV2"})
        self.dev2_host = self.config.get_api_host("DEV2")
        self.ran_inner_setup = True

        # THESE STATS ARE USED WHEN RUNNING THE LOAD RUNNER
        # connection options
        self.version = 4  # The version is explicitly specified on most tests
        self.node = 0  # node 0 is the VIP
        self.env = "DEV2"

        # test options
        self.api_call = {"User Recordings Ribbon": 1}  # the api_call is explicity specified on most tests
        self.n_min = 5
        self.n_max = 30

        # web options
        self.web_host = "localhost"
        self.no_web = False  # this is explicity specified on most tests
        self.n_clients = 240
        self.hatch_rate = 120
        self.time = "15s"
        self.exp_slaves = 16
        self.master_host_info = ("127.0.0.1", 5557)
        self.web_ui_host_info = ("localhost", 8089)
        self.load_runner = LoadRunner(self.master_host_info, self.web_ui_host_info, APITest.SLAVE_LOCUST_FILE,
                                      APITest.MASTER_LOCUST_FILE, self.config)

    def tearDown(self):
        try:
            self.PoolFactory.close()
        except:
            pass
        self.load_runner.stop_test()

    def _test_undistributed(self, route, version, web, assert_results=True):
        self.__empty_test_stats_folder()
        self.assertEqual(os.listdir(APITest.test_stats_folder), [], "The test_stats folder did not start empty")
        api_call_weight = {route: 1}
        if web:
            self.load_runner.run_single_core(api_call_weight, self.env, self.node, version, self.n_min, self.n_max,
                                             stats_file_name="test", stats_folder=APITest.test_stats_folder,
                                             )
            self.load_runner.run_from_ui(self.n_clients, self.hatch_rate)
            time.sleep(15)
        else:
            self.load_runner.run_single_core(api_call_weight, self.env, self.node, version, self.n_min, self.n_max,
                                             stats_file_name="test",
                                             no_web=True, reset_stats=True, num_clients=self.n_clients,
                                             hatch_rate=self.hatch_rate, run_time=self.time,
                                             stats_folder=APITest.test_stats_folder)
            info_list, return_code_list = self.load_runner.stop_test()
            for index in range(len(info_list)):
                self.assertEqual(0, return_code_list[index], str(info_list[index]))
        self.__check_test_stats_folder(assert_results)

    def _test_multi_core(self, route, version, web, assert_results=True):
        if self._is_multi_core_capable():
            self.load_runner.default_2_cores = False
        else:
            self.load_runner.default_2_cores = True
        self.__empty_test_stats_folder()
        self.assertEqual(os.listdir(APITest.test_stats_folder), [], "The test_stats folder did not start empty")
        api_call_weight = {route: 1}
        if web:
            self.load_runner.run_multi_core(api_call_weight, self.env, self.node, version, self.n_min, self.n_max,
                                            stats_file_name="test", stats_folder=APITest.test_stats_folder)
            self.load_runner.check_ui_slave_count()
            self.load_runner.run_from_ui(self.n_clients, self.hatch_rate)
            time.sleep(15)
        else:
            self.load_runner.run_multi_core(api_call_weight, self.env, self.node, version, self.n_min, self.n_max,
                                            stats_file_name="test", stats_folder=APITest.test_stats_folder,
                                            no_web=True, reset_stats=True, num_clients=self.n_clients,
                                            hatch_rate=self.hatch_rate, run_time=self.time)
            info_list, return_code_list = self.load_runner.stop_test()
            for index in range(len(info_list)):
                self.assertEqual(0, return_code_list[index], str(info_list[index]))
        self.__check_test_stats_folder(assert_results)

    def _is_multi_core_capable(self):
        return self.load_runner.cores > 1

    def __check_test_stats_folder(self, assert_results):
        requests_file = None
        distribution_file = None
        for file in os.listdir(APITest.test_stats_folder):
            if file.endswith("_requests.csv"):
                requests_file = os.path.join(APITest.test_stats_folder, file)
            elif file.endswith("_distribution.csv"):
                distribution_file = os.path.join(APITest.test_stats_folder, file)
        self.assertNotEqual(None, requests_file, "No requests file was found in the test directory")
        self.assertNotEqual(None, distribution_file, "The distribution file was not found in the test direcotyr")
        loaded_r_file = pandas.read_csv(requests_file, delimiter=',', quotechar='"', index_col=False)
        if assert_results:
            self.assertEqual(loaded_r_file["# failures"].tail(1).values[0], 0, "There were more than 0 failures")
            self.assertGreaterEqual(loaded_r_file["# requests"].tail(1).values[0], 400,
                                    "There were not enough requests sent out")

    def __empty_test_stats_folder(self):
        for file in os.listdir(APITest.test_stats_folder):
            os.remove(os.path.join(APITest.test_stats_folder, file))
        self.assertEqual(len(os.listdir(APITest.test_stats_folder)), 0,
                         "The test stats folder was not properly emptied")
