import json
import os
import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


import Load_Test.exceptions
import pandas as pd
import psutil
import shlex
import subprocess32 as sp
import logging
import math
import datetime
import time
from collections import namedtuple

import requests
from requests.exceptions import ConnectionError
import backoff
from Load_Test.exceptions import (SlaveInitilizationException, InvalidRoute, InvalidAPIEnv, InvalidPlaybackPlayer,
                                  InvalidPlaybackRoute, InvalidAPIVersion, InvalidAPINode, InvalidAPIVersionParams,
                                  InvalidCodec, OptionTypeError)
from Load_Test.Misc.environment_wrapper import (PlaybackEnvironmentWrapper as PlaybackWrap,
                                                APIEnvironmentWrapper as APIWrap,)
from Load_Test.Misc.utils import clean_stdout, size_key, API_VERSION_KEYS
from Load_Test.Data.request_pool import RequestPoolFactory


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
SECONDS = 1000

API_LOAD_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
locust_file_prefix = "Locust_Files"
PROJECT_DIR = os.path.dirname(API_LOAD_TEST_DIR)
LOCALVENV_DIR = os.path.join(PROJECT_DIR, "localVenv/")
VENV_DIR = os.path.join(PROJECT_DIR, "venv/")

STATS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Stats")
LOGS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Logs")
PLAYBACK_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, locust_file_prefix + "/playback_locust.py")
API_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, locust_file_prefix + "/api_locust.py")
DUMMY_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, locust_file_prefix + "/master_locust.py")





LocustFilePaths = namedtuple('LoucstFilePaths', ["master", "api", "playback"])

locust_file_paths = LocustFilePaths(DUMMY_LOCUST_FILE, API_LOCUST_FILE, PLAYBACK_LOCUST_FILE)
# TODO: Make salt stack configuration for build out on machines


class LoadRunner:

    assumed_load_average_added = 1
    assumed_cpu_used = 7
    Stat_Interval = 2
    total_used_cpu_running_threshold = 9  # TODO Find actual threshold
    process_age_limit = 2  # TODO Find process age limit
    Succesful_Test_Start = {"message": "Swarming started", "success": True}
    Succesful_Test_Stop = { "message": "Test stopped", "success": True}
    Max_Connection_Time = 5
    CPU_Measure_Interval = .2
    Boot_Time_Delay = 2.5  # TODO Find actual timing
    Max_Process_Wait_Time = 5
    UI_Action_Delay = 2

    # TODO: make a method to ensure the class is not running any proccesses from last run
    # TODO: make sure children is not tainted by automated_test in background
    def __init__(self, master_host_info, web_ui_info, config):
        self.master = None
        self.slaves = []
        self.master_host_info = master_host_info
        self.web_ui_host_info = web_ui_info
        self.config = config
        self.expected_slaves = 0
        self.__set_virtual_env()
        self._default_2_cores = False
        self._last_write_acton = time.time()
        self._last_boot_time = time.time()
        self._users = -1
        self._hatch_rate = -1

    @property
    def users(self):
        self.__post_boot_wait()
        if not self.children:
            return -1
        else:
            return self._get_ui_info()["user_count"]

    @property
    def state(self):
        if not self.children:
            return "idle"
        else:
            self.__post_boot_wait()
            try:
                state = self._ui_state()
            except ConnectionError:
                return "idle"
            else:
                if state in ["running", "hatching"]:
                    return "running"
                elif state in ["ready", "stopped"]:
                    return "setup"

    @property
    def last_boot(self):
        return self._last_boot_time

    @last_boot.setter
    def last_boot(self, value):
        max([child.create_time() for child in self.children])

    @property
    def last_write(self):
        return self._last_write_acton

    @last_write.setter
    def last_write(self, value):
        self._last_write_acton = time.time()

    @property
    def slaves_loaded(self):
        try:
            self.__assert_slave_count()
            return True
        except SlaveInitilizationException as e:
            return False

    @property
    def master(self):
        return self._master

    @master.setter
    def master(self, value):
        if not self.children:
            raise Load_Test.exceptions.LoadRunnerFailedClose(
                "Overrding Master child process prior to closing it, this will result in zombie processes")
        if not isinstance(value, sp.Popen) and value is not None:
            raise ValueError("You cannot assign the master process a value that is not a subprocess or None")
        self._master = value

    @property
    def slaves(self):
        return self._slaves

    @slaves.setter
    def slaves(self, value):
        if not self.children:
            raise Load_Test.exceptions.LoadRunnerFailedClose(
                "Overriding Slave child processes prior to closing it, this will result in zombie processes")
        if not isinstance(value, list):
            raise ValueError("You cannot assign the slaves process list a value that is not a list of subprocess")
        for process in value:
            if not isinstance(process, sp.Popen):
                raise ValueError("You cannot assign the slaves process list a value that is not a list of subprocess")
        self._slaves = value

    @property
    def children(self):
        return self.__child_processes()

    @property
    def cores(self):
        return self.__avaliable_cpu_count()

    @property
    def default_2_cores(self):
        return self._default_2_cores

    @default_2_cores.setter
    def default_2_cores(self, value):
        self._default_2_cores = value

    @property
    def running(self):
        if self.state is "idle":
            return False
        else:
            return True

#### Server Write Commands

    def _start_ui_load(self, locust_count, hatch_rate):
        self._users = locust_count
        self._hatch_rate = hatch_rate
        json_params = {"locust_count": locust_count, "hatch_rate": hatch_rate}
        response = self.__request_ui("post", extension="/swarm", data=json_params)
        if json.loads(response.content) != LoadRunner.Succesful_Test_Start:
            raise Load_Test.exceptions.FailedToStartLocustUI("The /swarm locust URL was accessed but the test was not properly started")
        self.last_write = time.time()

    def _stop_ui_test(self):
        self._users = -1
        self._hatch_rate = -1
        response = self.__request_ui("get", extension="/stop")
        if json.loads(response.content) != LoadRunner.Succesful_Test_Stop:
            raise Load_Test.exceptions.FailedToStartLocustUI("The /stop loocust URL was accessed but the test was not properly stopped")
        self.last_write = time.time()

    def _reset_stats(self):
        response = self.__request_ui("get", extension="/stats/reset")
        self.last_write = time.time()

#### Server Uitility Commands
    def _kill_test(self):
        try:
            info_list, return_codes = self.__fresh_state(False)
            self._users = -1
            self._hatch_rate = -1
            return info_list, return_codes
        except:
            raise


    def _run_distributed(self, env_options, master_locust_file, slave_locust_file):
        pass

    #TODO: change back
    def _run_multi_core(self, env_options, master_locust_file, slave_locust_file,
                        stats_file_name=None, log_level=None, log_file_name=None,
                        reset_stats=False,  stats_folder=None, log_folder=None):
        available_cores = self.__avaliable_cpu_count()
        if self.default_2_cores and available_cores < 2:
            available_cores = 2
        if available_cores <= 1:
            raise Load_Test.exceptions.NotEnoughAvailableCores(
                "There where only {cores} cores available for load test on this machine".format(
                    cores=available_cores))  # TO RUN MULTICORE WE NEED MORE THAN ONE CORE
        host = self.__get_host(env_options)
        self.expected_slaves = available_cores - 1
        stats_file_name, log_file_name = self.__get_file_paths(stats_folder, stats_file_name, log_folder, log_file_name)
        master_options = self.__create_master_options(host, master_locust_file, stats_file_name, log_level, log_file_name)
        slave_options = self.__create_slave_options(host, slave_locust_file, reset_stats)
        self.master = self.__create_process(env_options.get_env(), master_options)
        to_be_slaves = []
        env_options.max_slave_index = self.expected_slaves -1 # len(expected_slaves) -1 = max index
        env_options.slave_index = 0
        for index in range(self.expected_slaves):
            slave = self.__create_process(env_options.get_env(), slave_options)
            to_be_slaves.append(slave)
            env_options.slave_index += 1
        self.slaves = to_be_slaves
        self.last_boot = time.time()
        time.sleep(4)
        info_list, return_code = self._kill_test()
        print(info_list)
        print(return_code)
        print(master_options)
        print(slave_options)

    def _run_single_core(self, env_options, master_locust_file,
                         stats_file_name=None, log_level=None, log_file_name=None,
                         stats_folder=None, log_folder=None):

        stats_file_name, log_file_name = self.__get_file_paths(stats_folder, stats_file_name, log_folder, log_file_name)
        host = self.__get_host(env_options)
        undis_options = self.__create_undistributed_options(host, master_locust_file, stats_file_name, log_level,
                                                            log_file_name)
        self.master = self.__create_process(env_options.get_env(), undis_options)
        self.last_boot = time.time()

    def _is_running(self):
        state = self.state
        if state == "idle":
            return False
        elif state == "running":
            return True
        else:
            state = self.state
            if state == "running":
                return True
            else:
                return False

######################################## SERVER READ COMMANDS #########################################################
    def _get_ui_info(self, **kwargs):
        self.__post_action_wait()
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
        #for url in site_data["stats"]:
            # name = url["name"]
            # ui_info.setdefault(name, { "avg_content_length": url["avg_content_length"],
            #                            "rps": url["current_rps"],
            #                            "failures": url["num_failures"],
            #                            "requests": url["num_requests"]
            #                            }
            #                    )
        return ui_info

    def _ui_state(self):
        self.__post_action_wait()
        site_data = self._get_ui_info(headers={'Cache-Control': 'no-cache'})
        return site_data["state"]

    def _get_ui_request_distribution_stats(self):
        self.__post_action_wait()
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
        self.__post_action_wait()
        response = self.__request_ui("get", extension="/exceptions/csv")
        df = self.__response_to_pandas(response)
        return df

    def _get_pool_length(self, route, env, *args):
        pool_factory = RequestPoolFactory(self.config, 0, 0, 0, 0, None, [env])
        the_info = pool_factory.get_route_pool_and_ribbon(route, *args)
        if isinstance(the_info, dict):
            for item in the_info.values():
                return len(item.pool)
        else:
            return len(the_info)




#########################    THESE ARE THE HELPER FUNCTIONS   ###########################################################

    #These are options creation commands
    def _get_api_options(self, api_info, env, node, max_req, stat_interval,
                          assume_tcp, bin_by_resp_time, comp_idx=0, max_comp_idx=0):
        #TODO find easy way to set size for each api list we will be grabbing
        #1. Iterate through each api route key.
            #if its a route then go get the max size and set the size key
            #in the api locust setup when the locust is grabbing it's data set reset the size to the current size
        for api_route, api_version_info in api_info.items():
            if api_route.title() in self.config.api_routes:
                route_size = self._get_pool_length(api_route.title(), env, api_version_info, env)
                for version_info in api_version_info.values():
                    version_info[size_key] = route_size
        return APIWrap(api_info, node, env, max_req, assume_tcp, bin_by_resp_time, stat_interval,
                                 comp_idx, 0, max_comp_idx, 0, 0)

    def _get_playback_options(self, client, playback_route, quality, codecs, stat_interval, users, dvr, days_old,
                              comp_idx=0, max_comp_idx=0):
        overall_size = self._get_pool_length(playback_route, "DEV2", dvr, days_old, users)
        return PlaybackWrap(playback_route, quality, codecs, client, users, dvr, days_old, stat_interval,
                                    comp_idx, 0, max_comp_idx, 0, overall_size)



    #THESE ARE FILEPATH FUNCTIONS
    def __get_file_paths(self, stats_folder, stats_file_name, log_folder, log_file_name):
        if stats_folder is not None and stats_file_name is not None:
            stats_file_name = self.__get_file_path(stats_folder, stats_file_name)
        else:
            stats_file_name = self.__get_stats_location(stats_file_name) if stats_file_name is not None else None
        if log_folder is not None and log_file_name is not None:
            log_file_name = self.__get_file_path(log_folder, log_file_name)
        else:
            log_file_name = self.__get_log_location(log_file_name) if log_file_name is not None else None
        return stats_file_name, log_file_name

    def __get_stats_location(self, file_name):
        return self.__get_file_path(STATS_FOLDER, file_name)

    def __get_log_location(self, file_name):
        return self.__get_file_path(LOGS_FOLDER, file_name)

    def __get_file_path(self, folder_path, file_name):
        today = datetime.datetime.today().strftime('%Y-%m-%d-%H-%m')
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        todays_file = os.path.join(folder_path, "{today}_{name}".format(today=today, name=file_name))
        return todays_file

    #THESE ARE PROCESS STATE COMMANDS
    def __fresh_state(self, wait):
        """
        Helper method for _kill_test, use only if _kill_test doesn't suit your needs
        :param wait: How long to wait before killing the site
        :return: return_info (raw string), return codes [int]
        """
        return_info = []
        return_codes = []
        if wait:
            info, code = self.__safe_wait_kill(self.master)
        else:
            info, code = self.__safe_kill(self.master)
        return_codes.append(code)
        return_info.append(info)
        for slave in self.slaves:
            if wait:
                info, code = self.__safe_wait_kill(slave)
            else:
                info, code = self.__safe_kill(slave)
            return_codes.append(code)
            return_info.append(info)
        self.master = None
        self.slaves = []
        self.expected_slaves = 0
        if self.children:
            raise Load_Test.exceptions.LoadRunnerFailedClose("unsuccessfully closed all child processes")
        std_out_list = [clean_stdout(info_[0]) if info_[0] else "" for info_ in return_info]
        std_error_list = [clean_stdout(info_[1]) if info_[1] else "" for info_ in return_info]
        class ProcessInfo:
            def __init__(self, std_out, std_err):
                self._std_out = std_out
                self._std_err = std_err

            def __str__(self):
                return "\n_________________ERROR_______________\n" + self._std_err +\
                       "\n_________________OUT__________________\n" + self._std_out

            def __repr__(self):
                return str(self)

        return_info = [ProcessInfo(std_out_list[index], std_error_list[index]) for index in range(len(std_error_list))]
        return return_info, return_codes

    def __safe_wait_kill(self, process):
        if process is None:
            return "Process was None", -15
        try:
            return_code = process.wait(timeout=LoadRunner.Max_Process_Wait_Time)
            info = self.master.communicate()
        except sp.TimeoutExpired as e:
            info, return_code = self.__safe_kill(process)
        return info, return_code

    def __safe_kill(self, process):
        if process is None:
            return "Process was None", -15
        try:
            while process.poll() is None:
                process.kill()
            return_code = 0 if process.poll() == -9 else process.poll()
            info = process.communicate()
            return info, return_code
        except OSError as e:
            if e.strerror == "No such process":
                return str(e), -10
            else:
                raise e

    def __child_processes(self):
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        return children

    #THESE ARE PROCESS CREATION METHODS
    def __create_process(self, os_env, options):
        p = sp.Popen(options, env=os_env, stdout=sp.PIPE, stderr=sp.STDOUT, stdin=sp.PIPE, shell=True)
        return p

    def __create_master_options(self, host, master_locust_file, csv_file=None, log_level=None, log_file=None):

        # TODO: Use the web_ui_host stuff eventually (when incorporating with DCMNGR) (maybe, currently port forwarded
        web_ui_host = self.web_ui_host_info[0]
        web_ui_port = self.web_ui_host_info[1]
        masterbindHost = self.master_host_info[0]
        masterbindPort = self.master_host_info[1]
        locust_path = "locust"#self.__get_locust_file_dir()

        master_arg_string = "{locust} -f {master_file} -H {l_host} --master --master-bind-host={mb_host} --master-bind-port={mb_port}".format(
            locust=locust_path, master_file=master_locust_file, l_host=host, mb_host=masterbindHost, mb_port=masterbindPort
        )
        if csv_file is not None:
            master_arg_string = "{master_arg_string} --csv={file_name}".format(master_arg_string=master_arg_string,
                                                                               file_name=csv_file)
        if log_file is not None:
            master_arg_string = "{master_arg_string} --logfile={file_name}".format(master_arg_string=master_arg_string,
                                                                                   file_name=log_file)
        if log_level is not None:
            master_arg_string = "{master_arg_string} --loglevel={loglevel}".format(master_arg_string=master_arg_string,
                                                                                   loglevel=log_level)


        return shlex.split(master_arg_string)

    def __create_slave_options(self, host, slave_locust_file, reset_stats=False):
        masterhost = self.master_host_info[0]
        masterport = self.master_host_info[1]
        locust_path = "locust"#self.__get_locust_file_dir()

        slave_arg_string = "{locust} -f {slave_file} -H {l_host} --slave --master-host={m_host} --master-port={m_port}".format(
            locust = locust_path, slave_file=slave_locust_file, l_host=host, m_host=masterhost, m_port=masterport
        )
        if reset_stats:
            slave_arg_string = "{slave_arg_string} --reset-stats".format(slave_arg_string=slave_arg_string)

        return shlex.split(slave_arg_string)

    def __create_undistributed_options(self, host, locust_file, csv_file=None, log_level=None, log_file=None):

        # TODO: Use the web_ui_host stuff eventually (when incorporating with DCMNGR) maybe, currently port forwarding
        locust_path = "locust"#self.__get_locust_file_dir()

        undis_arg_string = "{locust} -f {undis_file} -H {l_host} ".format(
           locust=locust_path, undis_file=locust_file, l_host=host,
        )
        if csv_file is not None:
            undis_arg_string = "{undis_arg_string} --csv={file_name}".format(undis_arg_string=undis_arg_string,
                                                                             file_name=csv_file)
        if log_file is not None:
            undis_arg_string = "{undis_arg_string} --logfile={file_name}".format(undis_arg_string=undis_arg_string,
                                                                                 file_name=log_file)
        if log_level is not None:
            undis_arg_string = "{undis_arg_string} --loglevel={loglevel}".format(undis_arg_string=undis_arg_string,
                                                                                 loglevel=log_level)
        return shlex.split(undis_arg_string)

    #THESE ARE MISC HELPER FUNCTIONS
    def _users_property_function_wrapper(self):
        return self.users

    def __assert_slave_count(self):
        site_data = self._get_ui_info()
        slaves_count = site_data["slaves"]
        if self.expected_slaves is not slaves_count:
            raise Load_Test.exceptions.SlaveInitilizationException("All of the slaves where not loaded correctly")

    def __avaliable_cpu_count(self):
        """
        Takes samples of the system CPU usage to determine how many CPU's must be allocated to current system priceless
        Returns the amount of available physical CPU's that can be used for load testing
        :return:
        """
        physical_cores = psutil.cpu_count(
            logical=False)  # Get the # of hardware cores -- HyperThreading wont make a difference
        percentage_per_cpu = 100 / physical_cores
        idle_time_percentage = psutil.cpu_times_percent(
            LoadRunner.CPU_Measure_Interval).idle - LoadRunner.assumed_cpu_used
        available_cores_cpu = 0
        while idle_time_percentage >= percentage_per_cpu:
            idle_time_percentage -= percentage_per_cpu
            available_cores_cpu += 1

        load_avg = math.ceil(max(os.getloadavg()[:1]) + LoadRunner.assumed_load_average_added)
        available_cores_load_avg = physical_cores - load_avg if physical_cores > load_avg else 0

        available_cores = min(available_cores_cpu, available_cores_load_avg)
        return int(available_cores)

    def __response_to_pandas(self, response):
        io_string = StringIO(response.content)
        df = pd.read_csv(io_string, sep=",")
        return df

    def __set_virtual_env(self):
        activate_virtual_env_path = "bin/activate_this.py"
        if os.path.isdir(LOCALVENV_DIR):

            path = os.path.join(LOCALVENV_DIR, activate_virtual_env_path)
            execfile(path, dict(__file__=path))
        elif os.path.isdir(VENV_DIR):
            path = os.path.join(VENV_DIR, activate_virtual_env_path)
            execfile(path, dict(__file__=path))
        else:
            raise Exception("Could not find virutal env")

    def __get_host(self, options):
        if isinstance(options, APIWrap):
            host = self.config.get_api_host(options.env, options.node)
            return host
        elif isinstance(options, PlaybackWrap):
            host = self.config.get_api_host("DEV2", 0)
            return host

    @backoff.on_exception(backoff.expo,
                          ConnectionError,
                          max_time=Max_Connection_Time)
    def __request_ui(self, request, extension=None, **kwargs):
        self.__post_boot_wait()
        web_ui_host = self.web_ui_host_info[0]
        web_ui_port = self.web_ui_host_info[1]
        if web_ui_host in ["localhost", "127.0.0.1", "0.0.0.0"]:
            os.environ['no_proxy'] = '127.0.0.1,localhost'
            host = "http://{web_ui_host}:{web_ui_port}".format(web_ui_host=web_ui_host, web_ui_port=web_ui_port)
            host = host + extension if extension is not None else host
        else:
            host = "https://{web_ui_host}".format(web_ui_host=web_ui_host)
            host = host + extension if extension is not None else host
        response = requests.request(request, host, **kwargs)
        if response.status_code is not 200:
            raise Load_Test.exceptions.LocustUIUnaccessible("The web UI route {extension} could not be accessed".format(extension=extension))
        return response


######################################### VERIFICATION METHODS #########################################################

    def _verify_playback_options(self, client, playback_route, quality, codecs, users, dvr, days_old, stat_int):     #check dist loc info

        #check playback route
        if playback_route not in self.config.playback_routes:
            raise InvalidPlaybackRoute("{rte} Invalid Playback Route - Valid: {vld}".format(rte=playback_route,
                                                                                            vld=str(self.config.playback_routes)))
        #check playback client
        if client not in self.config.playback_players:
            raise InvalidPlaybackPlayer("{clt} Invalid Playback Player - Valid: {vld}".format(clt=client,
                                                                                              vld=str(self.config.playback_players)))
        #check plaback codec
        if not isinstance(codecs, list):
            if codecs and not isinstance(codecs[0], str):
                raise InvalidCodec("Invalid Playback Codec, codecs must be entered as list of strings")
        #check quality
        self.__verify_int("{} option".format(PlaybackWrap.QUALITY_KEY), quality)
        #check the stat_int
        self.__verify_int("{} option".format(PlaybackWrap.STAT_INT_KEY), stat_int)
        #Top N Playback is different than other routes
        if not playback_route == "Top N Playback":
            self.__verify_int("{} option".format(PlaybackWrap.USERS_KEY), users)
            self.__verify_int("{} option".format(PlaybackWrap.DVR_KEY), dvr)
            self.__verify_int("{} option".format(PlaybackWrap.DAYS_KEY), days_old)

    def _verify_api_params(self, api_call_weight, env, node, max_request, stat_interval, assume_tcp, bin_by_resp):
        #check dis locust
        self.__verify_api_call_weight(api_call_weight)
        self.__verify_env(env)
        self.__verify_node(env, node)
        self.__verify_bool("{} option".format(APIWrap.MAX_RPS_KEY), max_request)
        self.__verify_bool("{} option".format(APIWrap.ASSUME_TCP_KEY), assume_tcp)
        self.__verify_bool("{} option".format(APIWrap.BIN_RSP_TIME_KEY), bin_by_resp)
        if stat_interval:
            self.__verify_int("{} option".format(APIWrap.STAT_INT_KEY), stat_interval)

    def __verify_api_call_weight(self, api_call_weight):
        given_routes = api_call_weight.keys()
        #validate the route is an actual route
        for given_route in given_routes:
            if not self.config.is_route(given_route):
                raise InvalidRoute("{inv_route} is not a valid route".format(inv_route=given_route))
            route_params = api_call_weight[given_route]
            #validate the version is an actual version of the route
            for route_version in route_params.keys():
                if not self.config.is_version(given_route, int(route_version)):
                    raise InvalidAPIVersion("{version} is not a valid version for route {route}".format(
                        version=route_version, route=given_route
                    ))
                #verify the route contains all neccesary instance variables
                for neccesary_key in API_VERSION_KEYS:
                    if neccesary_key not in route_params[route_version].keys():
                        raise InvalidAPIVersionParams("{key} not in api_call {call} version {version}"
                                                    .format(key=neccesary_key, call=given_route, version=route_version))


    def __verify_env(self, env):
        if not self.config.is_api_env(env):
            raise InvalidAPIEnv("{env} is not a valid Env".format(env=env))

    def __verify_node(self, env, node):
        if not self.config.is_node(env, node):
            raise InvalidAPINode("{env} does not have node {inv_node}".format(
                env=env, inv_node=node
            ))

    def __verify_bool(self, name, should_be_bool):
        if not isinstance(should_be_bool, bool):
            error = "{name} should be a boolean".format(name=name)
            raise OptionTypeError(error)

    def __verify_int(self, name, should_be_int):
        if not isinstance(should_be_int, int):
            error = "{name} should be an int".format(name=name)
            raise OptionTypeError(error)

#################################################  WAIT METHODS  ########################################################

    def __post_action_wait(self):
        s_since = time.time() - self.last_write
        if s_since <= LoadRunner.UI_Action_Delay:
            to_sleep = LoadRunner.UI_Action_Delay - s_since
            time.sleep(to_sleep)

    def __post_boot_wait(self):
        s_since = time.time() - self.last_boot
        if s_since <= LoadRunner.Boot_Time_Delay:
            to_sleep = LoadRunner.Boot_Time_Delay - s_since
            time.sleep(to_sleep)
