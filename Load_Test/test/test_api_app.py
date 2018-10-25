from Load_Test.load_runner_api_wrapper import LoadRunnerAPIWrapper
from Load_Test.Misc.locust_test import LocustTest
import random
import backoff
import os
from requests.exceptions import ConnectionError
import json
from multiprocessing import Process
import requests
from main import main_func
from Load_Test.load_server_client import LoadServerClient

class TestAPIApp(LocustTest):

    def setUp(self):
        super(TestAPIApp, self).setUp()
        self.api_host_info = LoadRunnerAPIWrapper.web_api_host_info
        self.extension = LoadRunnerAPIWrapper.Extension
        self.server = Process(target=main_func, args=(True, LoadServerClient.local))
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



    def test_is_running_not_running(self):
        self._assert_not_running()


    def test_is_running_custom_running(self):
        self._assert_start_custom_test()
        self._assert_is_running()

    def test_is_running_automated_running(self):
        self._assert_start_automated_test()
        self._assert_is_running()


    def test_start_custom_test_custom_test_running(self):
        self._assert_start_custom_test()
        self._assert_failed_custom_start_other_test_already_running(LoadRunnerAPIWrapper.Current_Custom_Test_Msg)


    def test_start_custom_test_automated_test_running(self):
        self._assert_start_automated_test()
        self._assert_failed_custom_start_other_test_already_running(LoadRunnerAPIWrapper.Current_Automated_Test_Msg)

    def test_start_automated_test_custom_test_running(self):
        self._assert_start_custom_test()
        self._assert_failed_automated_start_other_test_already_running(LoadRunnerAPIWrapper.Current_Custom_Test_Msg)

    def test_start_automated_test_automated_test_running(self):
        self._assert_start_automated_test()
        self._assert_failed_automated_start_other_test_already_running(LoadRunnerAPIWrapper.Current_Automated_Test_Msg)


    #INVALID PARAMS

    def test_start_custom_invalid_api_routes(self):
        self._assert_custom_start_incorrect_params_test_run(u"Invalid is not a valid route", api_call={"Invalid": {1: None}})


    def test_start_custom_invalid_version(self):
        route = self.api_call.keys()[0]
        self._assert_custom_start_incorrect_params_test_run(u"-1 is not a valid version for route {route}".format(route=route), api_call={route: {-1: "Irrelevant"}})

    def test_start_custom_invalid_env(self):
        self._assert_custom_start_incorrect_params_test_run(u"INVALID is not a valid Env", env="INVALID")

    def test_start_custom_invalid_node(self):
        self._assert_custom_start_incorrect_params_test_run(u"{env} does not have node -1".format(env=self.env), node=-1)

    def test_start_benchmark_invalid_procedure(self):
        self._assert_automated_start_incorrect_params_test_run(u"{env} does not have node -1".format(env=self.env), node=-1)

    def test_start_automated_invalid_setup(self):
        pass








    def _assert_automated_start_incorrect_params_test_run(self, test_msg, **kwargs):
        expected_params = self.__get_start_automated_params(**kwargs)
        test_id, response = self.__remote_api_call("startAutomatedTest", expected_params)
        expected_error = {
            u'message': u'OtherError: {test_msg}'.format(test_msg=test_msg),
            u'code': 500, u'data': None, u'name': u'OtherError'}
        self.__assert_error(response, test_id, expected_error)


    def _assert_custom_start_incorrect_params_test_run(self, test_msg, **kwargs):
        expected_params = self.__get_start_custom_params(**kwargs)
        test_id, response = self.__remote_api_call("startCustomTest", expected_params)
        expected_error = {
            u'message': u'OtherError: {test_msg}'.format(test_msg=test_msg),
            u'code': 500, u'data': None, u'name': u'OtherError'}
        self.__assert_error(response, test_id, expected_error)


    def _assert_failed_custom_start_other_test_already_running(self, test_msg):
        expected_params = self.__get_start_custom_params()
        the_id, response = self.__remote_api_call("startCustomTest", expected_params)
        self.__assert_error(response, the_id, {
            u'message': u'OtherError: {test_msg}'.format(test_msg=test_msg),
            u'code': 500, u'data': None, u'name': u'OtherError'})

    def _assert_failed_automated_start_other_test_already_running(self, test_msg):
        expected_params = self.__get_start_automated_params()
        call_id, response = self.__remote_api_call("startAutomatedTest", expected_params)
        self.__assert_error(response, call_id, {
            u'message': u'OtherError: {test_msg}'.format(test_msg=test_msg),
            u'code': 500, u'data': None, u'name': u'OtherError'})


    def _assert_start_automated_test(self, **kwargs):
        expected_params = self.__get_start_automated_params(**kwargs)
        call_id, response = self.__remote_api_call("startAutomatedTest", expected_params)
        self.__assert_success(response, call_id, [True, LoadRunnerAPIWrapper.Current_Automated_Test_Msg])


    def _assert_stop_test(self):
        try:
            call_id, respone = self.__remote_api_call("stopTest", {})
            self.__assert_success(respone, call_id, False)
        except ConnectionError:
            pass


    def _assert_start_custom_test(self):
        expected_params = self.__get_start_custom_params()
        call_id, respone = self.__remote_api_call("startCustomTest", expected_params)
        self.__assert_success(respone, call_id, True)



    def _assert_is_running(self):
        call_id, response = self.__remote_api_call("isRunning", {})
        self.__assert_success(response, call_id, True)



    def _assert_not_running(self):
        call_id, response = self.__remote_api_call("isRunning", {})
        self.__assert_success(response, call_id, False)






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




    def __get_start_automated_params(self, **kwargs):
        setup_name     = kwargs["setup_name"] if "setup_name" in kwargs.keys() else self.setup_name
        procedure_name = kwargs["procedure_name"] if "procedure_name" in kwargs.keys() else self.procedure_name

        expected_params = {
            "setup_name": setup_name,
            "procedure_name": procedure_name
        }
        return expected_params




    def __get_start_custom_params(self, **kwargs):
        api_call = kwargs["api_call"] if "api_call" in kwargs.keys() else self.api_call
        env = kwargs["env"] if "env" in kwargs.keys() else self.env
        node = kwargs["node"] if "node" in kwargs.keys() else self.node
        max_request = kwargs["max_request"] if "max_request" in kwargs.keys() else self.max_request
        n_clients = kwargs["num_users"] if "num_users" in kwargs.keys() else self.n_clients
        hatch_rate = kwargs["hatch_rate"] if "hatch_rate" in kwargs.keys() else self.hatch_rate
        stat_interval = kwargs["stat_interval"] if "stat_interval" in kwargs.keys() else LoadRunnerAPIWrapper.Stat_Interval
        assume_tcp = kwargs["assume_tcp"] if "assume_tcp" in kwargs.keys() else False
        bin_by_resp = kwargs["bin_by_resp"] if "bin_by_resp" in kwargs.keys() else False
        expected_params = {
            "api_call_weight": api_call,
            "env": env,
            "node": node,
            "max_request": max_request,
            "num_users": n_clients,
            "hatch_rate": hatch_rate,
            "stat_interval": stat_interval,
            "assume_tcp": assume_tcp,
            "bin_by_resp": bin_by_resp
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





