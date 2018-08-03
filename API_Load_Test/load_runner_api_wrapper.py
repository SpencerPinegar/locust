from requests.exceptions import ConnectionError
from API_Load_Test.exceptions import TestAlreadyRunning, InvalidAPIRoute, InvalidAPIEnv, InvalidAPINode, \
    InvalidAPIVersion, LocustUIUnaccessible, SlaveInitilizationException, FailedToStartLocustUI

import os

API_Load_Test_Dir = os.path.dirname(os.path.abspath(__file__))
class LoadRunnerAPIWrapper:
    # TODO make come from config

    Stats_Folder = os.path.join(API_Load_Test_Dir, "Stats")
    Logs_Folder = os.path.join(API_Load_Test_Dir, "Load_Logs")
    Master_Locust_File = os.path.join(API_Load_Test_Dir, "master_locust.py")
    Slave_Locust_File = os.path.join(API_Load_Test_Dir, "api_locust.py")
    master_host_info = ("127.0.0.1", 5557)
    web_ui_host_info = ("localhost", 8089)
    web_api_host_info = ("localhost", 5000)
    test_runner_communication_info = ("127.0.0.1", 8000)

    Current_Benchmark_Test_Msg = u"A benchmark test is currently running on this server - It will not be available through the UI"
    Current_Manuel_Test_Msg = u"A manuel test is currently running on this server - view it through the UI"
    Setup_Benchmark_Test_Msg = u"A benchmark test is setup on this server - It will run and not be available through the UI"
    Setup_Manuel_Test_Msg = u"A manuel test is setup on this server - view/run it through the UI"


    def __init__(self, config, loadrunner):
        self.config = config
        self._test_runner = loadrunner


    @property
    def default_2_cores(self):
        return self._test_runner.default_2_cores

    @default_2_cores.setter
    def default_2_cores(self, value):
        self._test_runner.default_2_cores = value



    @property
    def test_runner(self):
        return self._test_runner

    @property
    def no_web(self):
        return self._test_runner.no_web

    def is_running(self):
        is_running = False
        test_type = None
        if self._test_runner.test_currently_running():
            is_running = True
            if self.no_web:
                test_type = self.Current_Benchmark_Test_Msg
            else:
                test_type = self.Current_Manuel_Test_Msg

        return (is_running, test_type)


    def is_setup(self):
        is_setup = True
        test_type = None
        is_running, running_test_type = self.is_running()
        if is_running:
            return False, running_test_type
        try:
            if self.no_web:
                if len(self._test_runner.children) is not self._test_runner.expected_slaves + 1:
                    raise SlaveInitilizationException("All of the slaves where not loaded correctly")
                test_type = self.Setup_Benchmark_Test_Msg
            else:
                self._test_runner.check_ui_slave_count()
                test_type = self.Setup_Manuel_Test_Msg
        except (SlaveInitilizationException, LocustUIUnaccessible, ConnectionError) as e:
            is_setup = False
            test_type = None
        finally:
            return is_setup, test_type


    def run_distributed(self, rps, api_call_weight, env, node, version, min, max):
        # TODO find a way to distribute segemented test data when running
        pass

    def setup_manuel_test(self, api_call_weight, env, node, version, min, max):
        self.__raise_if_running()
        self.stop_tests()
        self._verify_params(api_call_weight, env, version, node)
        file_prefix = "Manuel"
        self._test_runner.run_multi_core(api_call_weight, env, node, version, min, max,
                                            stats_file_name=file_prefix, stats_folder=LoadRunnerAPIWrapper.Stats_Folder,
                                            log_file_name=file_prefix, log_folder=LoadRunnerAPIWrapper.Logs_Folder,
                                            log_level="ERROR")

    def setup_and_start_benchmark_test(self, api_call_weight, env, node, version, min, max, num_clients, hatch_rate, run_time,
                                       reset_stats):
        self.__raise_if_running()
        self.stop_tests()
        self._verify_params(api_call_weight, env, version, node)
        file_prefix = "Benchmark"
        self._test_runner.run_multi_core(api_call_weight, env, node, version, min, max,
                                            stats_file_name=file_prefix, stats_folder=LoadRunnerAPIWrapper.Stats_Folder,
                                            log_file_name=file_prefix, log_folder=LoadRunnerAPIWrapper.Logs_Folder,
                                            log_level="ERROR",
                                            no_web=True, num_clients=num_clients, hatch_rate=hatch_rate,
                                            run_time=run_time, reset_stats=reset_stats)



    def start_manuel_from_ui(self, locust_count, hatch_rate):
        self.__raise_if_running()
        self._test_runner.run_from_ui(locust_count, hatch_rate)





    def stop_tests(self):
        self._test_runner.stop_test()





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


    def __raise_if_running(self):
        test_running, msg = self.is_running()
        if test_running:
            raise TestAlreadyRunning(msg)