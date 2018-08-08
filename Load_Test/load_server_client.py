import random
import requests
import backoff
from requests.exceptions import ConnectionError
import os
import json
from Load_Test.load_runner_api_wrapper import LoadRunnerAPIWrapper


extension = LoadRunnerAPIWrapper.Extension



class LoadServerClient:
    lgen8_host_name = "b-gp2-lgen-8.imovetv.com"
    lgen9_host_name = "b-gp2-lgen-9.imovetv.com"
    local = "127.0.0.1"

    def __init__(self, base_url, extension, port=LoadRunnerAPIWrapper.web_api_host_info[1]):
        self.base_url = base_url
        self.extension = extension
        self.port = port


    def ping(self):
        try:
            self.__remote_api_call("ping", {})
            return True
        except ConnectionError:
            return False

    def is_running(self):
        the_id, resp = self.__remote_api_call("isRunning", {})
        return self.__clean_resp(resp)

    def is_setup(self):
        the_id, resp = self.__remote_api_call("isSetup", {})
        return self.__clean_resp(resp)

    def stop_test(self):
        the_id,  resp =  self.__remote_api_call("stopTest", {})
        return self.__clean_resp(resp)

    def setup_manuel_test(self, api_call, env, node, version, n_min, n_max):
        params = self.__setup_test_params(api_call, env, node, version, n_min, n_max)
        call_id, respone = self.__remote_api_call("setupManuelTest", params)
        return self.__clean_resp(respone)

    def run_manuel_test(self, num_users, hatch_rate):
        params ={
            "num_users": num_users,
            "hatch_rate": hatch_rate
        }
        call_id, response = self.__remote_api_call("startManuelTest", params)
        return self.__clean_resp(response)


    def _setup_ts_segment_test(self):
        params = self.__setup_test_params({"Redundant Ts Segment": 1})
        call_id, response = self.__remote_api_call("setupManuelTest", params)
        return self.__clean_resp(response)


    def __remote_api_call(self, method, params, call_id = None):
        if call_id is None:
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
        if self.base_url in ["localhost", "127.0.0.1", "0.0.0.0"]:
            os.environ['no_proxy'] = '127.0.0.1, localhost'
        host = "http://{web_api_host}:{web_api_port}".format(web_api_host=self.base_url, web_api_port=self.port)
        host = host + self.extension
        response = requests.post(host, json=json)
        return response



    def __setup_test_params(self, api_call_weight, env="DEV2", node = 0, version = 1, n_min=5, n_max=30):
        params = {
            "api_call_weight": api_call_weight,
            "env": env,
            "node": node,
            "version": version,
            "n_min": n_min,
            "n_max": n_max
        }
        return params


    def __clean_resp(self, resp):
        if resp.status_code is 200:
            return json.loads(resp.content)
        else:
            return resp



