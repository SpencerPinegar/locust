from requests.exceptions import ConnectionError
from Load_Test.exceptions import (TestAlreadyRunning, WebOperationNoWebTest,
                                   LocustUIUnaccessible, SlaveInitilizationException,
                                  LostTestRunnerAPIObject)
from Load_Test.config import Config
from Load_Test.load_runner import LoadRunner
import time
import os

API_Load_Test_Dir = os.path.dirname(os.path.abspath(__file__))


class LoadRunnerAPIWrapper(LoadRunner):
    # TODO make come from config

    Stats_Folder = os.path.join(API_Load_Test_Dir, "Stats")
    Logs_Folder = os.path.join(API_Load_Test_Dir, "Load_Logs")
    Master_Locust_File = os.path.join(API_Load_Test_Dir, "master_locust.py")
    Slave_Locust_File = os.path.join(API_Load_Test_Dir, "api_locust.py")
    master_host_info = ("0.0.0.0", 5557)
    web_ui_host_info = ("0.0.0.0", 8089)
    web_api_host_info = ("0.0.0.0", 5000)
    test_runner_communication_info = ("0.0.0.0", 8000)

    Current_Benchmark_Test_Msg = u"A benchmark test is currently running on this server - It will not be available through the UI"
    Current_Manuel_Test_Msg = u"A manuel test is currently running on this server - view it through the UI"
    Setup_Benchmark_Test_Msg = u"A benchmark test is setup on this server - It will run and not be available through the UI"
    Setup_Manuel_Test_Msg = u"A manuel test is setup on this server - view/run it through the UI"
    TEST_API_WRAPPER = None
    Extension = '/LoadServer'

    @classmethod
    def setup(cls):
        config = Config()
        load_runner_api_wrapper = LoadRunnerAPIWrapper(LoadRunnerAPIWrapper.master_host_info, LoadRunnerAPIWrapper.web_ui_host_info,
                                 LoadRunnerAPIWrapper.Slave_Locust_File, LoadRunnerAPIWrapper.Master_Locust_File,
                                 config)
        LoadRunnerAPIWrapper.TEST_API_WRAPPER =load_runner_api_wrapper

    @classmethod
    def teardown(cls):
        if LoadRunnerAPIWrapper.TEST_API_WRAPPER is None:
            raise LostTestRunnerAPIObject("The Load Runner API Wrapper was None")
        else:
            LoadRunnerAPIWrapper.TEST_API_WRAPPER.stop_tests()

    def __init__(self, master_host_info, web_ui_info, slave_locust_file, master_locust_file, config):
        LoadRunner.__init__(self, master_host_info, web_ui_info, slave_locust_file, master_locust_file, config)


    def stop_tests(self):
        self._kill_test()

    def is_running(self, conn_error_raise=False):
        if conn_error_raise:
            to_catch = (LocustUIUnaccessible, SlaveInitilizationException)
        else:
            to_catch = (LocustUIUnaccessible, ConnectionError, SlaveInitilizationException)
        try:
            is_running = self._is_running()
            if not is_running:
                test_type = None
                return is_running, test_type
            if self.no_web:
                test_type = self.Current_Benchmark_Test_Msg
            else:
                test_type = self.Current_Manuel_Test_Msg
        except to_catch as e:
            is_running = False
            test_type = None
            return is_running, test_type
        else:
            return is_running, test_type

    def is_setup(self):
        try:
            is_running, type = self.is_running(conn_error_raise=True)
            if is_running:
                is_setup = False
                test_type = type
                return is_setup, test_type

            is_setup = self._is_setup()
            if not is_setup:
                test_type = None
                return is_setup, test_type
            if not is_setup:
                return is_setup, None
            if self.no_web:
                test_type = self.Setup_Benchmark_Test_Msg
            else:
                test_type = self.Setup_Manuel_Test_Msg
        except (SlaveInitilizationException, LocustUIUnaccessible, ConnectionError) as e:
            is_setup = False
            test_type = None
            return is_setup, test_type
        else:
            return is_setup, test_type

    def run_distributed(self, rps, api_call_weight, env, node, version, min, max):
        # TODO find a way to distribute segemented test data when running
        pass

    def setup_manuel_test(self, api_call_weight, env, node, version, min, max):
        self.__raise_if_running()
        self.stop_tests()
        self._verify_params(api_call_weight, env, version, node)
        file_prefix = "Manuel"
        self._run_multi_core(api_call_weight, env, node, version, min, max,
                                          stats_file_name=file_prefix, stats_folder=LoadRunnerAPIWrapper.Stats_Folder,
                                          log_file_name=file_prefix, log_folder=LoadRunnerAPIWrapper.Logs_Folder,
                                          log_level="ERROR")

    def setup_and_start_benchmark_test(self, api_call_weight, env, node, version, min, max, num_clients, hatch_rate,
                                       run_time,
                                       reset_stats):
        self.__raise_if_running()
        self.stop_tests()
        self._verify_params(api_call_weight, env, version, node)
        file_prefix = "Benchmark"
        self._run_multi_core(api_call_weight, env, node, version, min, max,
                                          stats_file_name=file_prefix, stats_folder=LoadRunnerAPIWrapper.Stats_Folder,
                                          log_file_name=file_prefix, log_folder=LoadRunnerAPIWrapper.Logs_Folder,
                                          log_level="ERROR",
                                          no_web=True, num_clients=num_clients, hatch_rate=hatch_rate,
                                          run_time=run_time, reset_stats=reset_stats)



    def start_manuel_from_ui(self, locust_count, hatch_rate):
        if self._is_setup():
            self._start_ui_load(locust_count, hatch_rate)
        else:
            if self.no_web:
                raise TestAlreadyRunning(self.Current_Benchmark_Test_Msg)
            else:
                raise WebOperationNoWebTest("The web UI has not been set up yet")


    def get_stats(self):
        dist_stats = self._get_ui_request_distribution_stats()
        info = self._get_ui_info()
        for api_call in dist_stats.keys():
            info[api_call].update(dist_stats[api_call])
        return info





    def __raise_if_running(self):
        test_running, msg = self.is_running()
        if test_running:
            raise TestAlreadyRunning(msg)
