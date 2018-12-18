from unittest import TestCase
from app.Data.config import Config
from app.Data.request_pool import RequestPoolFactory
from app.Core.load_runner import LoadRunner
import os
import pandas
import time
from app.Core.load_runner import locust_file_paths
from app.Data.data_factory import DataFactory
from app.Utils.utils import build_api_info
from collections import namedtuple
import sys



class LocustTest(TestCase):
    LOAD_TEST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEST_DIR = os.path.join(LOAD_TEST_DIR, "test")
    test_stats_folder = os.path.join(TEST_DIR, "test_stats")


    def setUp(self):
        self.expected_routes = {"User Recordings Ribbon", "User Franchise Ribbon", "User Recspace Information",
                                "Update User Settings",
                                "Create Recordings", "Protect Recordings", "Mark Watched", "Delete Recordings",
                                "Create Rules", "Update Rules",
                                "Delete Rules", "List Rules"}
        self.expected_api_env = {"DEV1", "DEV2", "DEV3", "QA", "BETA", "BETA2"}
        self.config = Config(debug=False)
        self.PoolFactory = RequestPoolFactory(self.config, 0, 0, 0, 0, None, envs={"DEV2"})
        self.dev2_recapi_host = self.config.recapi.get_host("DEV2")
        self.dev2_metadata_host = self.config.metadata.get_host("DEV2")
        self.ran_inner_setup = True
        self.min_requests = 50
        # THESE STATS ARE USED WHEN RUNNING THE LOAD RUNNER
        # connection options
        self.version = 4  # The version is explicitly specified on most tests
        self.assume_tcp = False
        self.bin_by_resp = False
        self.node = 0  # node 0 is the VIP
        self.env = "DEV2"
        self.api_call = {"User Recordings Ribbon": {
                                                    1: build_api_info(1, 20, 5, 30)
                                                    }
                        }
        self.test_api_call = {"Basic Network": {}}
        self.setup_name = "VIP User Recordings"
        self.procedure_name = "VIP Benchmark"

        # test options
        self.size = 10
        self.weight  = 15
        self.dvr = 1116
        self.asset_max_age = 100
        self.stat_int = 2
        self.max_request = False
        # web options
        self.web_host = "localhost"
        self.no_web = False  # this is explicity specified on most tests
        self.n_clients = 240
        self.hatch_rate = 120
        self.time = "20s"
        self.exp_slaves = 16
        self.master_host_info = ("127.0.0.1", 5557)
        self.web_ui_host_info = ("127.0.0.1", 8089)
        self.load_runner = LoadRunner(self.config)
        self.data_factory = DataFactory(config=self.config)


    def tearDown(self):
        try:
            self.PoolFactory.close()
        except:
            pass
        self.load_runner._kill_test()



    def _test_undistributed_playback(self, route, client, quality, codecs=[], assert_results = True):
        playback_options = self.__get_default_playback_options(route, client, quality, codecs, self.stat_int, 0, 0)
        self.__run_playback_locust(playback_options, False)
        if assert_results:
            self.__assert_successful_locust_run()


    def _test_multi_core_undistributed_playback(self, route, client, quality, codecs=[], assert_results=True):
        self.__force_multi_core()
        playback_options = self.__get_default_playback_options(route, client, quality, codecs, self.stat_int, 0, 0)
        self.__run_playback_locust(playback_options, True)
        if assert_results:
            self.__assert_successful_locust_run()

    def _test_multi_core_distributed_playback(self, route, client, quality, codecs=[], assert_results=True, kill_at_end=True):
        pass


    #TODO change back from running v1, v2, v4, v5
    def _test_undistributed_recapi(self, route, max_request, assume_tcp=False, bin_by_resp=False, version = None,
                                   assert_results=True):
        try:
            lb, ub = self.config.recapi.get_route_normal_min_max(route)
        except KeyError:
            lb, ub = 10, 10
        versions = self.config.recapi.get_route_versions(route)
        api_call_route_info = self.__get_default_recapi_route_info(route, version)
        # versions= [1]
        # route_api_call_weight = {}
        # for version in versions:
        #     route_api_call_weight.setdefault(int(version), build_api_info(self.weight, self.size, lb, ub))
        # api_call_route_info = {route: route_api_call_weight}
        self.__run_recapi_locust(api_call_route_info, max_request, assume_tcp, bin_by_resp, False)
        if assert_results:
            self.__assert_successful_locust_run()

    def _test_multi_core_undistributed_recapi_custom(self, api_route_info, max_request, assume_tcp=False,
                                                     bin_by_resp=False):
        self.__force_multi_core()
        self.__run_recapi_locust(api_route_info, max_request, assume_tcp, bin_by_resp, False)



    def _test_multi_core_undistributed_recapi(self, route, max_request, assume_tcp=False, bin_by_resp=False, version=None,
                                              assert_results=True):
        self.__force_multi_core()
        api_call_route_info = self.__get_default_recapi_route_info(route, version)
        self.__run_recapi_locust(api_call_route_info, max_request, assume_tcp, bin_by_resp, True)
        if assert_results:
            self.__assert_successful_locust_run()

    def _test_multi_core_distributed_recapi(self, route, max_request, version=None, assert_results=True, kill_at_end=True):
        pass


    def _test_undistributed_metadata(self, action, put_size, assert_results=True):
        metadata_options = self.__get_default_metdata_options(action, put_size)
        self.__run_metadata_locust(metadata_options, False)
        if assert_results:
            self.__assert_successful_locust_run()

    def _test_multi_core_undistributed_metadata(self, action, put_size, assert_results=True):
        self.__force_multi_core()
        metadata_options = self.__get_default_metdata_options(action, put_size)
        self.__run_metadata_locust(metadata_options, True)
        if assert_results:
            self.__assert_successful_locust_run()

    def _test_multi_core_distributed_metadata(self, action, put_size):
        pass

    def _is_multi_core_capable(self):
        return self.load_runner.cores > 1




    def __test_api_ratios(self, full_api_route, result_file):
        """
        Takes the api ratio and verifies that it is approximantly the correct ratio of request per version per item in
        api route
        :param full_api_route: { Route: { 1: {"weight": 2, .... , "size": 5}, 2: {...}}}
        :return: Bool True if it is approx the right ratio. approx = +-30%
        """
        def __get_count(route, version):

            return 1
        total_weight = 0
        total_count  = 0
        RouteVersionWeightCount = namedtuple("RouteVersionWeightCount", ["route", "version", "weight", "count"])
        api_info = []
        for route, route_details in full_api_route.items():
            for version, version_details in route_details.items():
                weight        = version_details["weight"]
                count         = __get_count(route, version)
                total_weight += weight
                total_count  += count
                api_info.append(RouteVersionWeightCount(route, version, weight, count))

        normal_counts_per_weight = float(total_count)/float(total_weight)
        for r_v_w_c in api_info:
            normal = r_v_w_c.weight*normal_counts_per_weight
            lb = r_v_w_c.count - normal*.3
            ub = r_v_w_c.count + normal*.3
            if not lb <= normal <= ub:
                return False
        return True



    def __get_default_metdata_options(self, action, put_size):
        return self.load_runner._get_metadata_options(action, put_size, self.env, self.node, self.stat_int)


    def __get_default_recapi_route_info(self, route, version):
        versions = self.config.recapi.get_route_versions(route) if version is None else [version]
        route_api_call_weight = {}
        try:
            lb, ub = self.config.recapi.get_route_normal_min_max(route)
            for version in versions:
                route_api_call_weight.setdefault(int(version), build_api_info(self.weight, self.size, lb, ub))
            api_call_weight = {route: route_api_call_weight}
        except KeyError:
            api_call_weight = {route: build_api_info(10, 10, 0, 0)}
        return api_call_weight


    def __get_default_playback_options(self, action, client, quality, codecs, stat_int, comp_idx, max_comp_idx):
        #size = self.load_runner.
        if action == "Top N Playback":
            n_clients = None
            dvr = None
            max_age = None
        else:
            n_clients = self.n_clients
            dvr = self.dvr
            max_age = self.asset_max_age
        return self.load_runner._get_playback_options(client, action, quality, codecs, stat_int, n_clients,
                                                          dvr, max_age, comp_idx, max_comp_idx)


    def __force_multi_core(self):
        if self._is_multi_core_capable():
            self.load_runner.default_2_cores = False
        else:
            self.load_runner.default_2_cores = True

    def __run_recapi_locust(self, api_info, max_request, assume_tcp, bin_by_resp, multicore):
        n_clients = 300 if max_request else self.n_clients
        options = self.load_runner._get_recapi_options(api_info, self.env, self.node, max_request,
                                                       self.config.stat_reporting_interval, assume_tcp, bin_by_resp)
        if multicore:
            self.load_runner._run_multi_core(options, locust_file_paths.web_host,
                                             locust_file_paths.api, stats_file_name="test",
                                             stats_folder=LocustTest.test_stats_folder)
            self.assertEqual(True, self.load_runner.slaves_loaded, "not all the slaves loaded correctly")
        else:
            self.load_runner._run_single_core(options, locust_file_paths.api,
                                              stats_file_name="test", stats_folder=LocustTest.test_stats_folder)
        self.load_runner.web_client.start_ramp_up(30, self.hatch_rate, True)
        time.sleep(10)


    def __run_metadata_locust(self, options, multicore):
        if multicore:
            self.load_runner._run_multi_core(options, locust_file_paths.web_host, locust_file_paths.metadata,
                                             stats_file_name="test", stats_folder=LocustTest.test_stats_folder)
            self.assertEqual(True, self.load_runner.slaves_loaded, "not all the slaves loaded correctly")
        else:
            self.load_runner._run_single_core(options, locust_file_paths.metadata, stats_file_name="test",
                                              stats_folder=LocustTest.test_stats_folder)
        self.load_runner.web_client.start_ramp_up(30, 1, True)
        time.sleep(10)




    def __run_playback_locust(self, options, multicore):
        if options.action == "Top N Playback":
            n_clients = len(self.PoolFactory.get_top_n_channels_in_last_day())
        else:
            n_clients = self.n_clients
        if multicore:
            self.load_runner._run_multi_core(options, locust_file_paths.web_host,
                                             locust_file_paths.playback, stats_file_name="test",
                                             stats_folder=LocustTest.test_stats_folder)
            self.assertEqual(True, self.load_runner.slaves_loaded, "not all the slaves loaded correctly")
        else:
            self.load_runner._run_single_core(options, locust_file_paths.playback,
                                              stats_file_name="test", stats_folder=LocustTest.test_stats_folder)
        self.load_runner.web_client.start_ramp_up(n_clients, 1, True)
        time.sleep(20)


    def __assert_successful_locust_run(self):
        stats = self.load_runner.get_stats()
        failure_rate = stats["fail_ratio"]
        num_requests = stats['num requests']
        self.assertGreater(num_requests, 0, "The locust run did not send any requests out")
        self.assertLess(failure_rate, 5, "The locust run failed 5% or more of requests - Failure Rate: {}%".format(failure_rate))
        self.assertGreater(num_requests, 100, "The locust run sent out less than 100 requests - Requests: {}".format(num_requests))

