from requests.exceptions import ConnectionError
from Load_Test.exceptions import (TestAlreadyRunning, WebOperationNoWebTest,
                                   LocustUIUnaccessible, SlaveInitilizationException,
                                  LostTestRunnerAPIObject)
from Load_Test.Data.config import Config
from Load_Test.load_runner import LoadRunner, locust_file_paths, PLAYBACK_LOCUST_FILE

import time
import os
from Load_Test.automated_test_case import AutomatedTestCase
from Load_Test.Data.route_relations import RoutesRelation


API_Load_Test_Dir = os.path.dirname(os.path.abspath(__file__))


class LoadRunnerAPIWrapper(LoadRunner):
    """
    This is a class that exposes api functions to the world and conceals the underlying complex load_runner.
    It is able to remember it's own state by keeping a single load runner as a class value
    """
    # TODO make come from config

    Stats_Folder = os.path.join(API_Load_Test_Dir, "Stats")
    Logs_Folder = os.path.join(API_Load_Test_Dir, "Load_Logs")
    Master_Locust_File = os.path.join(API_Load_Test_Dir, "master_locust.py")
    Slave_Locust_File = os.path.join(API_Load_Test_Dir, "api_locust.py")
    master_host_info = ("0.0.0.0", 5557)
    web_ui_host_info = ("0.0.0.0", 8089)
    web_api_host_info = ("0.0.0.0", 5000)
    test_runner_communication_info = ("0.0.0.0", 8000)

    Current_Automated_Test_Msg = u"An automated test is currently running on this server - view it through the UI"
    Current_Custom_Test_Msg = u"A custom test is currently running on this server - view it through the UI"
    TEST_API_WRAPPER = None
    Extension = '/LoadServer'




    @classmethod
    def setup(cls):

        config = Config()
        load_runner_api_wrapper = LoadRunnerAPIWrapper(LoadRunnerAPIWrapper.master_host_info,
                                                       LoadRunnerAPIWrapper.web_ui_host_info, config)
        LoadRunnerAPIWrapper.TEST_API_WRAPPER = load_runner_api_wrapper

    @classmethod
    def teardown(cls):
        if LoadRunnerAPIWrapper.TEST_API_WRAPPER is None:
            raise LostTestRunnerAPIObject("The Load Runner API Wrapper was None")
        else:
            LoadRunnerAPIWrapper.TEST_API_WRAPPER.stop_tests()


    @property
    def is_automated_test(self):
        return self.automated_test != None

    def __init__(self, master_host_info, web_ui_info, config):
        LoadRunner.__init__(self, master_host_info, web_ui_info, config)
        self.automated_test = None


    def stop_tests(self):
        self._kill_test()

    def is_running(self):
        return self._is_running()



    def run_distributed(self, rps, api_call_weight, env, node, version, min, max):
        # TODO find a way to distribute segemented test data when running
        pass




    def custom_playback_test(self, client, playback_route, quality, codecs, users=None, dvr=None, days_old=None,
                             stat_int=2):
        self.__raise_if_running()
        self.stop_tests()
        self._verify_playback_options(client, playback_route, quality, codecs, users, dvr, days_old, stat_int)
        options = self._get_playback_options(client, playback_route, quality, codecs, users, dvr, days_old)
        self._run_multi_core(options, locust_file_paths.master, locust_file_paths.playback)




    def custom_api_test(self, api_info, env, node, max_request, stat_interval=None,
                        assume_tcp=False, bin_by_resp=False):
        self.__raise_if_running()
        self.stop_tests()
        self._verify_api_params(api_info, env, node, max_request, stat_interval, assume_tcp, bin_by_resp)
        file_prefix = "Custom API"
        options = self._get_api_options(api_info, env, node, max_request, stat_interval, assume_tcp, bin_by_resp)
        self._run_multi_core(options, locust_file_paths.master, locust_file_paths.api,
                             stats_file_name=file_prefix, stats_folder=LoadRunnerAPIWrapper.Stats_Folder,
                             log_file_name=file_prefix, log_folder=LoadRunnerAPIWrapper.Logs_Folder,
                             log_level="ERROR")



    def custom_api_to_failure(self, api_call_weight, env, node, stat_interval=None):
        self.__raise_if_running()
        self.stop_tests()
        #Here are some constants of this test
        file_prefix = "Failure API"
        max_reqeust = False
        assume_tcp = False
        bin_by_resp = True
        self._verify_api_params(api_call_weight, env, node, max_reqeust, stat_interval, assume_tcp, bin_by_resp)






    def run_automated_test_case(self, setup_name, procedure_name):
        #TODO implement way to run benchmark test
        self.__raise_if_running()
        self.stop_tests()
        #way to verify setup and procedure name
        #way to get all information and format it into the _run_nulti_core method
        file_prefix = "Automated"
        self.automated_test = AutomatedTestCase(setup_name, procedure_name,
                                                LoadRunnerAPIWrapper.TEST_API_WRAPPER,
                                                LoadRunnerAPIWrapper.Stat_Interval)
        self.automated_test.run()


    def start_ramp_up(self, locust_count, hatch_rate, first_start=False):
        state = self.state
        if state == "idle":
            raise WebOperationNoWebTest("The web UI has not been set up yet")
        elif state == "setup":
            self._start_ui_load(locust_count, hatch_rate)
        else:
            if state == "running" and not first_start:
                self._start_ui_load(locust_count, hatch_rate)
            else:
                raise TestAlreadyRunning(self.Current_Custom_Test_Msg)


    def get_stats(self):
        default_total = {'99%': 0, '80%': 0, '75%': 0, '90%': 0, '66%': 0, '50%': 0, '100%': 0, 'num requests': 0, '98%': 0}
        dist_stats = self._get_ui_request_distribution_stats()
        info = self._get_ui_info()
        total = dist_stats.pop("Total", default_total)
        for key, value in total.items():
            info.setdefault(key, value)
        info.setdefault("stats", dist_stats)
        info.pop("state", None)
        return info


    def reset_stats(self):
        if self.is_running():
            self._reset_stats()
        else:
            raise WebOperationNoWebTest("The web UI has not been set up and started yet")


    def __raise_if_running(self):
        test_running = self.is_running()
        if test_running:
            if self.is_automated_test:
                raise TestAlreadyRunning(LoadRunnerAPIWrapper.Current_Automated_Test_Msg)
            else:
                raise TestAlreadyRunning(LoadRunnerAPIWrapper.Current_Custom_Test_Msg)





