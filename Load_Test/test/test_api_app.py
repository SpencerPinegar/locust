from Load_Test.load_runner_api_wrapper import LoadRunnerAPIWrapper
from Load_Test.api_test import APITest
import random
import backoff
import os
from requests.exceptions import ConnectionError
import json
from multiprocessing import Process
import requests
from main import main_func

class TestAPIApp(APITest):

    def setUp(self):
        super(TestAPIApp, self).setUp()
        self.api_host_info = LoadRunnerAPIWrapper.web_api_host_info
        self.extension = LoadRunnerAPIWrapper.Extension
        self.server = Process(target=main_func, args=(True,))
        self.server.start()


    def tearDown(self):
        self._assert_stop_test()
        self.server.terminate()
        self.server.join()
        super(TestAPIApp, self).tearDown()


    def test_ping_on(self):
        call_id, response = self.__remote_api_call("ping", {})
        self.__assert_success(response, call_id, u"alive")

    def test_ping_off(self):
        self.server.terminate()
        self.server.join()
        with self.assertRaises(ConnectionError):
            response = self.__remote_api_call("ping", {})


    def test_is_setup_not_running_not_setup(self):
        self._assert_not_setup(None)



    def test_is_setup_manuel_setup_not_running(self):
        self._assert_setup_manuel_test()
        self._assert_is_setup(LoadRunnerAPIWrapper.Setup_Manuel_Test_Msg)


    def test_is_setup_manuel_setup_and_running(self):
        self._assert_setup_manuel_test()
        self._assert_start_manuel_test()
        self._assert_is_running(LoadRunnerAPIWrapper.Current_Manuel_Test_Msg)
        self._assert_not_setup(LoadRunnerAPIWrapper.Current_Manuel_Test_Msg)



    def test_is_setup_setup_and_run_benchmark(self):
        self._assert_setup_and_run_benchmark()
        self._assert_not_setup(LoadRunnerAPIWrapper.Current_Benchmark_Test_Msg)

    def test_is_running_not_setup_not_running(self):
        self._assert_not_running()


    def test_is_running_manuel_setup_not_running(self):
        self._assert_setup_manuel_test()
        self._assert_not_running()


    def test_is_running_manuel_setup_and_running(self):
        self._assert_setup_manuel_test()
        self._assert_start_manuel_test()
        self._assert_is_running(LoadRunnerAPIWrapper.Current_Manuel_Test_Msg)

    def test_is_running_benchmark_setup_and_running(self):
        self._assert_setup_and_run_benchmark()
        self._assert_is_running(LoadRunnerAPIWrapper.Current_Benchmark_Test_Msg)

    def test_start_manuel_manuel_test_not_setup_not_running(self):
        self._assert_cant_start_unsetup_manuel()

    def test_start_manuel_manuel_test_setup_not_running(self):
        self._assert_setup_manuel_test()
        self._assert_start_manuel_test()


    def test_start_manuel_manuel_test_setup_and_running(self):
        self._assert_setup_manuel_test()
        self._assert_start_manuel_test()
        self._assert_failed_manuel_start_other_test_already_running(LoadRunnerAPIWrapper.Current_Manuel_Test_Msg)


    def test_start_manuel_benchmark_running(self):
        self._assert_setup_and_run_benchmark()
        self._assert_failed_manuel_start_other_test_already_running(LoadRunnerAPIWrapper.Current_Benchmark_Test_Msg)

    def test_start_benchmark_not_setup_not_running(self):
        self._assert_setup_and_run_benchmark()

    def test_start_benchmark_manuel_setup_not_running(self):
        self._assert_setup_manuel_test()
        self._assert_setup_and_run_benchmark()

    def test_start_benchmark_manuel_setup_and_running(self):
        self._assert_setup_manuel_test()
        self._assert_start_manuel_test()
        self._assert_failed_benchmark_start_other_test_already_running(LoadRunnerAPIWrapper.Current_Manuel_Test_Msg)

    def test_start_benchmark_benchmark_running(self):
        self._assert_setup_and_run_benchmark()
        self._assert_failed_benchmark_start_other_test_already_running(LoadRunnerAPIWrapper.Current_Benchmark_Test_Msg)


    #INVALID PARAMS

    def test_start_manuel_invalid_api_routes(self):
        self._assert_manuel_setup_incorrect_params_test_run(u"Invalid is not a valid route", api_call={"Invalid": 12})

    def test_start_benchmark_invalid_api_routes(self):
        self._assert_benchmark_setup_incorrect_params_test_run(u"Invalid is not a valid route", api_call={"Invalid": 12})

    def test_start_manuel_invalid_version(self):
        route = self.api_call.keys()[0]
        self._assert_manuel_setup_incorrect_params_test_run(u"-1 is not a valid version for route {route}".format(route=route), version=-1)

    def test_start_benchmark_invalid_version(self):
        route = self.api_call.keys()[0]
        self._assert_benchmark_setup_incorrect_params_test_run(u"-1 is not a valid version for route {route}".format(route=route), version=-1)

    def test_start_manuel_invalid_env(self):
        self._assert_manuel_setup_incorrect_params_test_run(u"INVALID is not a valid Env", env="INVALID")

    def test_start_benchmark_invalid_env(self):
        self._assert_benchmark_setup_incorrect_params_test_run(u"INVALID is not a valid Env", env="INVALID")

    def test_start_manuel_invalid_node(self):
        self._assert_manuel_setup_incorrect_params_test_run(u"{env} does not have node -1".format(env=self.env), node=-1)

    def test_start_benchmark_invalid_node(self):
        self._assert_benchmark_setup_incorrect_params_test_run(u"{env} does not have node -1".format(env=self.env), node=-1)











    def _assert_manuel_setup_incorrect_params_test_run(self, test_msg, **kwargs):
        expected_params = self.__get_setup_manuel_params(**kwargs)
        test_id, response = self.__remote_api_call("setupManualTest", expected_params)
        expected_error = {
            u'message': u'OtherError: {test_msg}'.format(test_msg=test_msg),
            u'code': 500, u'data': None, u'name': u'OtherError'}
        self.__assert_error(response, test_id, expected_error)


    def _assert_benchmark_setup_incorrect_params_test_run(self, test_msg, **kwargs):
        expected_params = self.__get_benchmark_test_params(**kwargs)
        test_id, response = self.__remote_api_call("startBenchmarkTest", expected_params)
        expected_error = {
            u'message': u'OtherError: {test_msg}'.format(test_msg=test_msg),
            u'code': 500, u'data': None, u'name': u'OtherError'}
        self.__assert_error(response, test_id, expected_error)


    def _assert_failed_manuel_start_other_test_already_running(self, test_msg):

        expected_params = self.__get_start_manuel_params()
        the_id, response = self.__remote_api_call("startManualTest", expected_params)
        self.__assert_error(response, the_id, {
            u'message': u'OtherError: {test_msg}'.format(test_msg=test_msg),
            u'code': 500, u'data': None, u'name': u'OtherError'})

    def _assert_failed_benchmark_start_other_test_already_running(self, test_msg):
        expected_params = self.__get_benchmark_test_params()
        call_id, response = self.__remote_api_call("startBenchmarkTest", expected_params)
        self.__assert_error(response, call_id, {
            u'message': u'OtherError: {test_msg}'.format(test_msg=test_msg),
            u'code': 500, u'data': None, u'name': u'OtherError'})

    def _assert_cant_start_unsetup_manuel(self):
        expected_params = self.__get_start_manuel_params()
        call_id, response = self.__remote_api_call("startManualTest", expected_params)
        self.__assert_error(response, call_id,
                            {u'message': u'OtherError: The /swarm locust URL could not be accessed', u'code': 500,
                             u'data': None, u'name': u'OtherError'})

    def _assert_setup_and_run_benchmark(self, **kwargs):
        expected_params = self.__get_benchmark_test_params(**kwargs)
        call_id, response = self.__remote_api_call("startBenchmarkTest", expected_params)
        self.__assert_success(response, call_id, [True, LoadRunnerAPIWrapper.Current_Benchmark_Test_Msg])


    def _assert_stop_test(self):
        try:
            call_id, respone = self.__remote_api_call("stopTest", {})
            self.__assert_success(respone, call_id, [False, None])
        except ConnectionError as e:
            pass


    def _assert_setup_manuel_test(self):
        expected_params =self.__get_setup_manuel_params()
        call_id, response = self.__remote_api_call("setupManualTest", expected_params)
        self.__assert_success(response, call_id, [True, LoadRunnerAPIWrapper.Setup_Manuel_Test_Msg])


    def _assert_start_manuel_test(self):
        expected_params = self.__get_start_manuel_params()
        call_id, respone = self.__remote_api_call("startManualTest", expected_params)
        self.__assert_success(respone, call_id, [True, LoadRunnerAPIWrapper.Current_Manuel_Test_Msg])



    def _assert_is_running(self, Type_MSG):
        call_id, response = self.__remote_api_call("isRunning", {})
        self.__assert_success(response, call_id, [True, Type_MSG])



    def _assert_not_running(self):
        call_id, response = self.__remote_api_call("isRunning", {})
        self.__assert_success(response, call_id, [False, None])

    def _assert_is_setup(self, Type_MSG):
        call_id, response = self.__remote_api_call("isSetup", {})
        self.__assert_success(response, call_id, [True, Type_MSG])



    def _assert_not_setup(self, Type_MSG):
        call_id, response = self.__remote_api_call("isSetup", {})
        self.__assert_success(response, call_id, [False, Type_MSG])




    def __assert_success(self, response, expected_id, expected_ressult):
        self.assertEqual(200, response.status_code, "The api server was not reached successfully")
        content = json.loads(response.content)
        with self.assertRaises(KeyError):
            shouldnt_exist = content["error"]
        self.assertEqual(expected_id, content["id"], "An unexpected request was returned")
        self.assertEqual(expected_ressult, content["result"])

    def __assert_error(self, response, expected_id, expected_error):
        self.assertEqual(200, response.status_code, "The api server was not reached successfully")
        content = json.loads(response.content)
        with self.assertRaises(KeyError):
            shouldnt_exit = content["result"]
        self.assertEqual(expected_id, content["id"], "An unexpected request was returned")
        self.assertEqual(expected_error, content["error"])




    def __get_benchmark_test_params(self, **kwargs):
        expected_params = self.__get_setup_manuel_params(**kwargs)

        n_clients   = kwargs["clients"] if "clients" in kwargs.keys() else self.n_clients
        hatch_rate  = kwargs["hatch_rate"] if "hatch_rate" in kwargs.keys() else self.hatch_rate
        run_time    = kwargs["run_time"] if "run_time" in kwargs.keys() else self.time
        reset_stats = kwargs["reset_stats"] if "reset_stats" in kwargs.keys() else False

        expected_params.setdefault("num_clients", n_clients)
        expected_params.setdefault("hatch_rate", hatch_rate)
        expected_params.setdefault("run_time", run_time)
        expected_params.setdefault("reset_stats", reset_stats)
        return expected_params

    def __get_setup_manuel_params(self, **kwargs):
        api_call = kwargs["api_call"] if "api_call" in kwargs.keys() else self.api_call
        env = kwargs["env"] if "env" in kwargs.keys() else self.env
        node = kwargs["node"] if "node" in kwargs.keys() else self.node
        version = kwargs["version"] if "version" in kwargs.keys() else self.version
        n_min = kwargs["min"] if "min" in kwargs.keys() else self.n_min
        n_max = kwargs["max"] if "max" in kwargs.keys() else self.n_max
        expected_params = {
            "api_call_weight": api_call,
            "env": env,
            "node": node,
            "version": version,
            "n_min": n_min,
            "n_max": n_max
        }
        return expected_params


    def __get_start_manuel_params(self, **kwargs):
        n_clients = kwargs["clients"] if "clients" in kwargs.keys() else self.n_clients
        hatch_rate = kwargs["hatch_rate"] if "hatch_rate" in kwargs.keys() else self.hatch_rate
        expected_params = {
            "num_users": n_clients,
            "hatch_rate": hatch_rate
        }
        return expected_params




    def __remote_api_call(self, method, params):
        call_id = random.randint(1, 200)
        json = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": call_id
        }
        response = self.__request_api(json)
        return call_id, response


    @backoff.on_exception(backoff.expo,
                          ConnectionError,
                          max_time=4)
    def __request_api(self, json):
        web_api_host = self.api_host_info[0]
        web_api_port = self.api_host_info[1]
        if web_api_host in["localhost", "127.0.0.1", "0.0.0.0"]:
            os.environ['no_proxy'] = '127.0.0.1,localhost'
        host = "http://{web_api_host}:{web_api_port}".format(web_api_host=web_api_host, web_api_port=web_api_port)
        host = host + self.extension

        response = requests.post(host, json=json)
        return response





