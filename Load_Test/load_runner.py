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

import requests
from requests.exceptions import ConnectionError
import backoff
from Load_Test.exceptions import SlaveInitilizationException


from Load_Test.environment_wrapper import EnvironmentWrapper as EnvWrap

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
SECONDS = 1000

API_LOAD_TEST_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.dirname(API_LOAD_TEST_DIR)
LOCALVENV_DIR = os.path.join(PROJECT_DIR, "localVenv/")
VENV_DIR = os.path.join(PROJECT_DIR, "venv/")

STATS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Stats")
LOGS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Logs")

SLAVE_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "api_locust.py")
MASTER_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "master_locust.py")


# TODO: Make salt stack configuration for build out on machines


class LoadRunner:
    assumed_load_average_added = 1
    assumed_cpu_used = 7
    stat_interval = 2
    total_used_cpu_running_threshold = 9  # TODO Find actual threshold
    process_age_limit = 2  # TODO Find process age limit
    Succesful_Test_Start = {"message": "Swarming started", "success": True}
    Max_Connection_Time = 2.5
    CPU_Measure_Interval = .2
    Locust_Boot_Time = 2.5  # TODO Find actual timing
    Max_Process_Wait_Time = 5
    Run_From_UI_Delay = 2

    # TODO: make a method to ensure the class is not running any proccesses from last run

    def __init__(self, master_host_info, web_ui_info, slave_locust_file, master_locust_file, config):
        self.master = None
        self.slaves = []
        self.master_locust_file = master_locust_file
        self.slave_locust_file = slave_locust_file
        self.master_host_info = master_host_info
        self.web_ui_host_info = web_ui_info
        self.config = config
        self.no_web = None
        self.expected_slaves = 0
        self.__set_virtual_env()
        self._default_2_cores = False

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
    def no_web(self):
        return self._no_web

    @no_web.setter
    def no_web(self, value):
        if self._no_web is None:
            self._no_web = value
        else:
            if not self.master or not self.slaves:
                raise Load_Test.exceptions.LoadRunnerFailedClose(
                    "You can not change the web status of a test without closing the previous test")

    @property
    def children(self):
        return self._child_processes()

    @property
    def cores(self):
        return self._avaliable_cpu_count()

    @property
    def default_2_cores(self):
        return self._default_2_cores

    @default_2_cores.setter
    def default_2_cores(self, value):
        self._default_2_cores = value

    def run_multi_core(self, api_call_weight, env, node, version, n_min, n_max,
                       stats_file_name=None, log_level=None, log_file_name=None, no_web=False,
                       reset_stats=False, num_clients=None, hatch_rate=None, run_time=None,
                       stats_folder=None, log_folder=None):
        self.no_web = no_web
        available_cores = self._avaliable_cpu_count()
        if self.default_2_cores:
            available_cores = 2
        if available_cores <= 1:
            raise Load_Test.exceptions.NotEnoughAvailableCores(
                "There where only {cores} cores available for load test on this machine".format(
                    cores=available_cores))  # TO RUN MULTICORE WE NEED MORE THAN ONE CORE

        self.expected_slaves = available_cores - 1
        os_env = self._get_configured_env(api_call_weight, env, version, node, n_min, n_max)
        stats_file_name, log_file_name = self._get_file_paths(stats_folder, stats_file_name, log_folder, log_file_name)

        master_options = self._create_master_options(env, node, stats_file_name, log_level, log_file_name, no_web,
                                                     reset_stats,
                                                     self.expected_slaves, num_clients, hatch_rate, run_time)
        slave_options = self._create_slave_options(env, node, reset_stats)

        self.master = self._create_process(os_env.get_env(), master_options)

        to_be_slaves = []
        for index in range(self.expected_slaves):
            slave = self._create_process(os_env.get_env(), slave_options)
            to_be_slaves.append(slave)
        self.slaves = to_be_slaves
        self._wait_for_locust_process_upboot()

    def run_single_core(self, api_call_weight, env, node, version, n_min, n_max, stats_file_name=None, log_level=None,
                        log_file_name=None,
                        no_web=False, reset_stats=False, num_clients=None, hatch_rate=None, run_time=None,
                        stats_folder=None, log_folder=None):
        self.no_web = no_web
        stats_file_name, log_file_name = self._get_file_paths(stats_folder, stats_file_name, log_folder, log_file_name)
        os_env = self._get_configured_env(api_call_weight, env, version, node, n_min, n_max)

        undis_options = self._create_undistributed_options(env, node, stats_file_name, log_level, log_file_name, no_web,
                                                           reset_stats,
                                                           num_clients, hatch_rate, run_time)
        self.master = self._create_process(os_env.get_env(), undis_options)
        self._wait_for_locust_process_upboot()

    def run_from_ui(self, locust_count, hatch_rate):
        json_params = {"locust_count": locust_count, "hatch_rate": hatch_rate}
        try:
            response = self.__request_ui("post", extension="/swarm", data=json_params)
        except ConnectionError as e:
            raise Load_Test.exceptions.FailedToStartLocustUI("The /swarm locust URL could not be accessed")
        else:
            if response.status_code is not 200:
                raise Load_Test.exceptions.FailedToStartLocustUI("The /swarm locust URL could not be accessed")
            elif json.loads(response.content) != LoadRunner.Succesful_Test_Start:
                raise Load_Test.exceptions.FailedToStartLocustUI("The /swarm locust URL was accessed but the test was not properly started")
            else:
                time.sleep(LoadRunner.Run_From_UI_Delay)



    def grab_ui_request_info_stats(self):
        response = self.__request_ui("get", extension="/stats/requests/csv")
        return self.__response_to_pandas(response)


    def grab_ui_request_distribution_stats(self):
        response = self.__request_ui("get", extension="/stats/distribution/csv")
        return self.__response_to_pandas(response)

    def grab_ui_exception_info(self):
        response = self.__request_ui("get", extension="/exceptions/csv")
        return self.__response_to_pandas(response)



    def is_running(self):

        children = self.children
        if not children:
            return False
        elif self.no_web is True:
            return True
        else:
            state = self._ui_state()
            if state == "running" or state == "hatching":
                return True
            else:
                return False

    def is_setup(self):
        children = self.children
        if not children:
            return False
        elif self.no_web is True:
            if len(self.children) is not self.expected_slaves + 1:
                raise SlaveInitilizationException("All of the slaves where not loaded correctly")
            return False
        else:

            state = self._ui_state()
            if state == "ready":# or state =="stopped":#TODO: if stopped
                self._check_ui_slave_count()
                return True
            else:
                return False


    def stop_test(self):
        try:
            if self.no_web:
                info_list, return_codes = self.__fresh_state(True)
            else:
                info_list, return_codes = self.__fresh_state(False)
            return info_list, return_codes
        except:
            raise



    def __fresh_state(self, wait):
        return_info = []
        return_codes = []
        if wait:
            info, code = self._safe_wait_kill(self.master)
        else:
            info, code = self._safe_kill(self.master)
        return_codes.append(code)
        return_info.append(info)
        for slave in self.slaves:
            if wait:
                info, code = self._safe_wait_kill(slave)
            else:
                info, code = self._safe_kill(slave)
            return_codes.append(code)
            return_info.append(info)
        self.master = None
        self.slaves = []
        self.expected_slaves = 0
        if self.children:
            raise Load_Test.exceptions.LoadRunnerFailedClose("unsuccesfully closed all child proccesses")
        return return_info, return_codes


    def _safe_wait_kill(self, process):
        if process is None:
            return "Process was None", -15
        try:
            return_code = process.wait(timeout=LoadRunner.Max_Process_Wait_Time)
            info = self.master.communicate()
        except sp.TimeoutExpired as e:
            info, return_code = self._safe_kill(process)
        return info, return_code

    def _safe_kill(self, process):
        if process is None:
            return "Process was None", -15
        try:
            while process.poll() is None:
                process.kill()
            return_code = 0 if process.poll() == -9 else process.poll()
            info = process.communicate()
            if None is return_code:
                print("what")
            return info, return_code
        except OSError as e:
            if e.strerror == "No such process":
                return str(e), -10
            else:
                raise e

    def _avaliable_cpu_count(self):
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

        load_avg = math.ceil(max(os.getloadavg()[:2]) + LoadRunner.assumed_load_average_added)
        available_cores_load_avg = physical_cores - load_avg if physical_cores > load_avg else 0

        available_cores = min(available_cores_cpu, available_cores_load_avg)
        return int(available_cores)

    def _get_file_paths(self, stats_folder, stats_file_name, log_folder, log_file_name):
        if stats_folder is not None and stats_file_name is not None:
            stats_file_name = self.__get_file_path(stats_folder, stats_file_name)
        else:
            stats_file_name = self._get_stats_location(stats_file_name) if stats_file_name is not None else None
        if log_folder is not None and log_file_name is not None:
            log_file_name = self.__get_file_path(log_folder, log_file_name)
        else:
            log_file_name = self._get_log_location(log_file_name) if log_file_name is not None else None
        return stats_file_name, log_file_name

    def _get_stats_location(self, file_name):
        return self.__get_file_path(STATS_FOLDER, file_name)

    def _get_log_location(self, file_name):
        return self.__get_file_path(LOGS_FOLDER, file_name)

    def __get_file_path(self, folder_path, file_name):
        today = datetime.datetime.today().strftime('%Y-%m-%d-%H-%m')
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        todays_file = os.path.join(folder_path, "{today}_{name}".format(today=today, name=file_name))
        return todays_file

    def _child_processes(self):
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        return children

    def _create_process(self, os_env, options):
        p = sp.Popen(options, env=os_env, stdout=sp.PIPE, stderr=sp.STDOUT, stdin=sp.PIPE)
        return p

    def _get_configured_env(self, api_call_weight, env, version, node, normal_min, normal_max):
        my_env = EnvWrap(os.environ.copy(), API_CALL_WEIGHT=api_call_weight, VERSION=version,
                         NODE=node, ENV=env, N_MIN=normal_min, N_MAX=normal_max, STAT_INTERVAL=LoadRunner.stat_interval)
        return my_env

    def _create_master_options(self, env, node, csv_file=None, log_level=None, log_file=None, no_web=False,
                               reset_stats=False, expected_slaves=None, num_clients=None, hatch_rate=None,
                               run_time=None):

        # TODO: Use the web_ui_host stuff eventually (when incorporating with DCMNGR)
        host = self.config.get_api_host(env, node)
        web_ui_host = self.web_ui_host_info[0]
        web_ui_port = self.web_ui_host_info[1]
        masterbindHost = self.master_host_info[0]
        masterbindPort = self.master_host_info[1]
        locust_path = "locust"#self.__get_locust_file_dir()

        master_arg_string = "{locust} -f {master_file} -H {l_host} --master --master-bind-host={mb_host} --master-bind-port={mb_port}".format(
            locust=locust_path, master_file=self.master_locust_file, l_host=host, mb_host=masterbindHost, mb_port=masterbindPort
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

        if no_web:
            assert expected_slaves is not None, "expected_slaves param required to run locust in no web state"
            assert num_clients is not None, "num_clients param required to run locust in no web state"
            assert hatch_rate is not None, "hatch_rate param required to run locust in no web state"
            assert run_time is not None, "run_time param required to run locust in no web state"
            assert csv_file is not None, "csv_file param required to run locust in no web state"
            master_arg_string = "{master_arg_string} --no-web -c {n_clients} -r {n_hatch} -t {n_time} --expect-slaves={e_slaves}".format(
                master_arg_string=master_arg_string, n_clients=num_clients, n_hatch=hatch_rate, n_time=run_time,
                e_slaves=expected_slaves
            )
            if reset_stats:
                master_arg_string = "{master_arg_string} --reset-stats".format(master_arg_string=master_arg_string)

        return shlex.split(master_arg_string)

    def _create_slave_options(self, env, node, reset_stats=False):
        host = self.config.get_api_host(env, node)
        masterhost = self.master_host_info[0]
        masterport = self.master_host_info[1]
        locust_path = "locust"#self.__get_locust_file_dir()

        slave_arg_string = "{locust} -f {slave_file} -H {l_host} --slave --master-host={m_host} --master-port={m_port}".format(
            locust = locust_path, slave_file=self.slave_locust_file, l_host=host, m_host=masterhost, m_port=masterport
        )
        if reset_stats:
            slave_arg_string = "{slave_arg_string} --reset-stats".format(slave_arg_string=slave_arg_string)

        return shlex.split(slave_arg_string)

    def _create_undistributed_options(self, env, node, csv_file=None, log_level=None, log_file=None, no_web=False,
                                      reset_stats=False, num_clients=None, hatch_rate=None, run_time=None):

        # TODO: Use the web_ui_host stuff eventually (when incorporating with DCMNGR)
        host = self.config.get_api_host(env, node)
        locust_path = "locust"#self.__get_locust_file_dir()

        undis_arg_string = "{locust} -f {undis_file} -H {l_host} ".format(
           locust=locust_path, undis_file=self.slave_locust_file, l_host=host,
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

        if no_web:
            assert num_clients is not None, "num_clients param required to run locust in no web state"
            assert hatch_rate is not None, "hatch_rate param required to run locust in no web state"
            assert run_time is not None, "run_time param required to run locust in no web state"
            assert csv_file is not None, "csv_file param required to run locust in no web state"
            undis_arg_string = "{undis_arg_string} --no-web -c {n_clients} -r {n_hatch} -t {n_time}".format(
                undis_arg_string=undis_arg_string, n_clients=num_clients, n_hatch=hatch_rate, n_time=run_time
            )
            if reset_stats:
                undis_arg_string = "{undis_arg_string} --reset-stats".format(undis_arg_string=undis_arg_string)

        return shlex.split(undis_arg_string)

    def _ui_state(self):
        site_data = self.__ui_info(headers={'Cache-Control': 'no-cache'})
        return site_data["state"]


    def _check_ui_slave_count(self):
        site_data = self.__ui_info()
        try:
            slaves_count = len(site_data["slaves"])
        except KeyError as e:
            slaves_count = 0
        if self.expected_slaves is not slaves_count:
            raise Load_Test.exceptions.SlaveInitilizationException("All of the slaves where not loaded correctly")



    def _wait_for_locust_process_upboot(self):
        while time.time() - min([child.create_time() for child in self.children]) < LoadRunner.Locust_Boot_Time:
            time.sleep(.1)


    def __response_to_pandas(self, response):
        if response.status_code is not 200:
            raise Load_Test.exceptions.LocustUIUnaccessible("The web UI could not be accessed")
        else:
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


    def __ui_info(self, **kwargs):
        response = self.__request_ui("get", extension="/stats/requests", **kwargs)
        if response.status_code is not 200:
            raise Load_Test.exceptions.LocustUIUnaccessible("The web UI could not be accessed")
        site_data = json.loads(response.content)
        return site_data

    @backoff.on_exception(backoff.expo,
                          ConnectionError,
                          max_time=Max_Connection_Time)
    def __request_ui(self, request, extension=None, **kwargs):
        if self.no_web:
            raise Load_Test.exceptions.AttemptAccessUIWhenNoWeb("Locust is running in no web mode, you can't access the web UI")
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
        return response




