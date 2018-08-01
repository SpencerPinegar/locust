from API_Load_Test.load_runner import LoadRunner
from API_Load_Test.Config.config import Config
from API_Load_Test.api_exceptions import TestAlreadyRunning, InvalidAPIRoute, InvalidAPIEnv, InvalidAPINode, \
    InvalidAPIVersion, UnaccessibleLocustUI, SlaveInitilizationException

import os
import requests
import json
import time

API_Load_Test_Dir = os.path.dirname(os.path.abspath(__file__))
class TestAPIWrapper:
    # TODO make come from config

    Stats_Folder = os.path.join(API_Load_Test_Dir, "Stats")
    Logs_Folder = os.path.join(API_Load_Test_Dir, "Load_Logs")
    Master_Locust_File = os.path.join(API_Load_Test_Dir, "master_locust.py")
    Slave_Locust_File = os.path.join(API_Load_Test_Dir, "api_locust.py")
    master_host_info = ("127.0.0.1", 5557)
    web_ui_host_info = ("localhost", 8089)
    web_api_host_info = ("0.0.0.0", 5000)
    test_runner_communication_info = ("127.0.0.1", 8000)

    Current_Benchmark_Test_Msg = u"A benchmark test is currently running on this server - It will not be available through the UI"
    Current_Manuel_Test_Msg = u"A manuel test is currently running on this server - view it through the UI"

    def __init__(self):
        self.config = Config()
        self._test_runner = LoadRunner(TestAPIWrapper.master_host_info, TestAPIWrapper.web_ui_host_info,
                                       TestAPIWrapper.Slave_Locust_File, TestAPIWrapper.Master_Locust_File, self.config)

    @property
    def test_runner(self):
        return self._test_runner

    @property
    def no_web(self):
        return self.test_runner.no_web

    def is_test_running(self):
        is_running = False
        test_type = None
        if self.test_runner.test_currently_running():
            is_running = True
            if self.no_web:
                test_type = self.Current_Benchmark_Test_Msg
            else:
                test_type = self.Current_Manuel_Test_Msg

        return (is_running, test_type)

    def run_distributed(self, rps, api_call_weight, env, node, version, min, max):
        # TODO find a way to distribute segemented test data when running
        pass

    def start_manuel_test(self, api_call_weight, env, node, version, min, max):
        test_running, msg = self.is_test_running()
        if test_running:
            raise TestAlreadyRunning(msg)
        else:
            self.test_runner.stop_test()
            self._verify_params(api_call_weight, env, version, node)
            file_prefix = "Manuel"
            self.test_runner.run_multi_core(api_call_weight, env, node, version, min, max,
                                            stats_file_name=file_prefix, stats_folder=TestAPIWrapper.Stats_Folder,
                                            log_file_name=file_prefix, log_folder=TestAPIWrapper.Logs_Folder,
                                            log_level="ERROR")

    def start_benchmark_test(self, api_call_weight, env, node, version, min, max, num_clients, hatch_rate, run_time,
                             reset_stats):
        test_running, msg = self.is_test_running()
        if test_running:
            raise TestAlreadyRunning(msg)
        else:
            self.test_runner.stop_test()
            self._verify_params(api_call_weight, env, version, node)
            file_prefix = "Benchmark"
            self.test_runner.run_multi_core(api_call_weight, env, node, version, min, max,
                                            stats_file_name=file_prefix, stats_folder=TestAPIWrapper.Stats_Folder,
                                            log_file_name=file_prefix, log_folder=TestAPIWrapper.Logs_Folder,
                                            log_level="ERROR",
                                            no_web=True, num_clients=num_clients, hatch_rate=hatch_rate,
                                            run_time=run_time, reset_stats=reset_stats)

    def verify_started(self):
        if self.no_web:
            if len(self.test_runner.children) is not self.test_runner.expected_slaves + 1:
                raise SlaveInitilizationException("All of the slaves where not loaded correctly")
        else:
            self.__check_ui_slave_count()
        return u"started"

    def _verify_params(self, api_call_weight, env, version, node):
        self.__verify_api_routes(api_call_weight)
        self.__verify_version(api_call_weight, version)
        self.__verify_env(env)
        self.__verify_node(env, node)

    def __verify_api_routes(self, api_call_weight):
        given_routes = api_call_weight.keys()
        for given_route in given_routes:
            if not self.config.is_route(given_route):
                raise InvalidAPIRoute("{inv_route} is not a valid route".format(inv_route=given_route))

    def __verify_env(self, env):
        if not self.config.is_api_env(env):
            raise InvalidAPIEnv("{env} is not a valid Env".format(env=env))

    def __verify_node(self, env, node):
        if not self.config.is_node(env, node):
            raise InvalidAPINode("{env} does not have node {inv_node}".format(
                env=env, inv_node=node
            ))

    def __verify_version(self, api_call_weight, version):
        route_names = api_call_weight.keys()
        for route_name in route_names:
            if not self.config.is_version(route_name, version):
                raise InvalidAPIVersion("{version} is not a valid version for route {route}".format(
                    version=version, route=route_name
                ))

    def __check_ui_slave_count(self, retries=2):
        tries = 0
        while True:
            try:
                response = self.__request_ui("get", extension="/stats/requests")
                if response.status_code is not 200:
                    raise UnaccessibleLocustUI("The web UI could not be accessed")
                site_data = json.loads(response.content)
                slaves_count = len(site_data["slaves"])
                if self.test_runner.expected_slaves is not slaves_count:
                    raise SlaveInitilizationException("All of the slaves where not loaded correctly")
            except UnaccessibleLocustUI or SlaveInitilizationException as e:
                tries += 1
                if tries >= retries:
                    raise e
                time.sleep(1)
            else:
                return

    def __request_ui(self, request, extension=None, **kwargs):
        web_ui_host = self.web_ui_host_info[0]
        web_ui_port = self.web_ui_host_info[1]
        if web_ui_host == "localhost":
            os.environ['no_proxy'] = '127.0.0.1,localhost'
            host = "http://{web_ui_host}:{web_ui_port}".format(web_ui_host=web_ui_host, web_ui_port=web_ui_port)
            host = host + extension if extension is not None else host
            response = requests.request(request, host, **kwargs)
        else:
            host = "https://{web_ui_host}".format(web_ui_host=web_ui_host)
            host = host + extension if extension is not None else host
            response = requests.request(request, host, **kwargs)
        return response
