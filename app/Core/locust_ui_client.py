import json
import os
import sys
import logging

if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

import pandas as pd
from collections import namedtuple
import requests
from requests.exceptions import ConnectionError
import backoff
from app.Core.exceptions import (WebOperationNoWebTest, TestAlreadyRunning, FailedToStartLocustUI,
                                 LocustUIUnaccessible)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
SECONDS = 1000

API_LOAD_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
locust_file_prefix = "Locust_App"
PROJECT_DIR = os.path.dirname(API_LOAD_TEST_DIR)

STATS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Stats")
LOGS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Load_Logs")
PLAYBACK_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, locust_file_prefix + "/playback_locust.py")
API_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, locust_file_prefix + "/api_locust.py")
DUMMY_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, locust_file_prefix + "/master_locust.py")

LocustFilePaths = namedtuple('LoucstFilePaths', ["web_host", "api", "playback"])

locust_file_paths = LocustFilePaths(DUMMY_LOCUST_FILE, API_LOCUST_FILE, PLAYBACK_LOCUST_FILE)


# TODO: Make salt stack configuration for build out on machines
def _max_time():
    return LocustUIClient.Max_wait

class LocustUIClient(object):
    Succesful_Test_Start = {"message": "Swarming started", "success": True}
    Succesful_Test_Stop = {"message": "Test stopped", "success": True}
    Max_wait = None

    # TODO: make a method to ensure the class is not running any proccesses from last run
    # TODO: make sure children is not tainted by automated_test in background
    def __init__(self, host, port, max_wait_time):
        self.host = host
        self.port = port
        LocustUIClient.Max_wait = max_wait_time

    ########################################################################################################################
    ##########################################  Server Write  ##############################################################
    ########################################################################################################################

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
                raise TestAlreadyRunning("CURRENT TEST RUNNING")
        self.__wait_till_running()

    def reset_stats(self):
        try:
            self._reset_stats()
        except ConnectionError:
            raise WebOperationNoWebTest("The web UI has not been set up and started yet")

    def stop_test(self):
        self._stop_ui_test()

    ########################################################################################################################
    ##########################################  Server Read   ##############################################################
    ########################################################################################################################
    @property
    def users(self):
        try:
            return self._get_ui_info()["user_count"]
        except ConnectionError:
            return -1

    @property
    def state(self):
        try:
            site_data = self._get_ui_info(headers={'Cache-Control': 'no-cache'})
            state = site_data["state"]
        except ConnectionError:
            return "idle"
        else:
            if state in ["running", "hatching"]:
                return "running"
            elif state in ["ready", "stopped"]:
                return "setup"

    @property
    def slave_count(self):
        site_data = self._get_ui_info()
        return site_data["slaves"]

    @property
    def stats(self):
        default_total = {'99%': 0, '80%': 0, '75%': 0, '90%': 0, '66%': 0, '50%': 0, '100%': 0, 'num requests': 0,
                         '98%': 0}
        dist_stats = self._get_ui_request_distribution_stats()
        info = self._get_ui_info()
        total = dist_stats.pop("Total", default_total)
        for key, value in total.items():
            info.setdefault(key, value)
        info.setdefault("stats", dist_stats)
        info.pop("state", None)
        return info

        ########################################################################################################################
        ##########################################  Server Read  HELPERS #######################################################
        ########################################################################################################################

    def _get_ui_info(self, **kwargs):
        response = self.__request_ui("get", extension="/stats/requests", **kwargs)
        site_data = json.loads(response.content)
        ui_info = {}
        ui_info.setdefault("errors", site_data["errors"])
        ui_info.setdefault("fail_ratio", site_data["fail_ratio"])
        ui_info.setdefault("user_count", site_data["user_count"])
        ui_info.setdefault("state", site_data["state"])

        try:
            slaves_count = len(site_data["slaves"])
        except KeyError as e:
            slaves_count = 0
        ui_info.setdefault("slaves", slaves_count)
        # for url in site_data["stats"]:
        # name = url["name"]
        # ui_info.setdefault(name, { "avg_content_length": url["avg_content_length"],
        #                            "rps": url["current_rps"],
        #                            "failures": url["num_failures"],
        #                            "requests": url["num_requests"]
        #                            }
        #                    )
        return ui_info

    def _get_ui_request_distribution_stats(self):
        response = self.__request_ui("get", extension="/stats/distribution/csv")
        df = self.__response_to_pandas(response)
        json_data = {}
        for index, row in df.iterrows():
            name = row["Name"]
            name = name.replace("POST ", "").replace("GET ", "")
            num_requests = row["# requests"]
            p_50 = row["50%"]
            p_66 = row["66%"]
            p_75 = row["75%"]
            p_80 = row["80%"]
            p_90 = row["90%"]
            p_98 = row["98%"]
            p_99 = row["99%"]
            p_100 = row["100%"]
            json_data.setdefault(name, {"num requests": num_requests,
                                        "50%": p_50,
                                        "66%": p_66,
                                        "75%": p_75,
                                        "80%": p_80,
                                        "90%": p_90,
                                        "98%": p_98,
                                        "99%": p_99,
                                        "100%": p_100
                                        })
        return json_data

    def _get_ui_exception_info(self):
        response = self.__request_ui("get", extension="/exceptions/csv")
        df = self.__response_to_pandas(response)
        return df

    ########################################################################################################################
    ##########################################  Server Write  HELPERS ######################################################
    ########################################################################################################################

    def _start_ui_load(self, locust_count, hatch_rate):
        self._users = locust_count
        self._hatch_rate = hatch_rate
        json_params = {"locust_count": locust_count, "hatch_rate": hatch_rate}
        response = self.__request_ui("post", extension="/swarm", data=json_params)
        if json.loads(response.content) != LocustUIClient.Succesful_Test_Start:
            raise FailedToStartLocustUI(
                "The /swarm locust URL was accessed but the test was not properly started")

    def _stop_ui_test(self):
        self._users = -1
        self._hatch_rate = -1
        response = self.__request_ui("get", extension="/stop")
        if json.loads(response.content) != LocustUIClient.Succesful_Test_Stop:
            raise FailedToStartLocustUI(
                "The /stop loocust URL was accessed but the test was not properly stopped")

    def _reset_stats(self):
        response = self.__request_ui("get", extension="/stats/reset")

    ########################################################################################################################
    ##########################################  MISC HELPERS  ##############################################################
    ########################################################################################################################

    def __response_to_pandas(self, response):
        io_string = StringIO(response.content)
        df = pd.read_csv(io_string, sep=",")
        return df

    @backoff.on_exception(backoff.constant,
                          ConnectionError,
                          max_time=_max_time)
    def __request_ui(self, request, extension=None, **kwargs):
        web_ui_host = self.host
        web_ui_port = self.port
        if web_ui_host in ["localhost", "127.0.0.1", "0.0.0.0"]:
            host = "http://{web_ui_host}:{web_ui_port}".format(web_ui_host=web_ui_host, web_ui_port=web_ui_port)
            host = host + extension if extension is not None else host
        else:
            host = "https://{web_ui_host}".format(web_ui_host=web_ui_host)
            host = host + extension if extension is not None else host
        response = requests.request(request, host, **kwargs)
        if response.status_code is not 200:
            raise LocustUIUnaccessible(
                "The web UI route {extension} could not be accessed".format(extension=extension))
        return response

    def __wait_till_running(self):
        retries = 0
        while True:
            our_state = self.state
            if our_state != "running":
                if retries < 3:
                    retries = + 1
                else:
                    raise ConnectionError("LOCUST UI WAS NOT EVER RUN")
            else:
                break


