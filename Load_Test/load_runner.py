import os
import sys

if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

import Load_Test.exceptions

import psutil
import logging
import math
import datetime
import time
from collections import namedtuple
from multiprocessing import Pool
from requests.exceptions import ConnectionError
from Load_Test.exceptions import (SlaveInitilizationException, InvalidRoute, InvalidAPIEnv, InvalidPlaybackPlayer,
                                  InvalidPlaybackRoute, InvalidAPIVersion, InvalidAPINode, InvalidAPIVersionParams,
                                  InvalidCodec, OptionTypeError, TestAlreadyRunning)
from Load_Test.Misc.environment_wrapper import (PlaybackEnvironmentWrapper as PlaybackWrap,
                                                APIEnvironmentWrapper as APIWrap, )
from Load_Test.Misc.utils import size_key, API_VERSION_KEYS
from Load_Test.Data.request_pool import RequestPoolFactory
from Load_Test.automated_test_case import AutomatedTestCase
from Load_Test.locust_ui_client import LocustUIClient
from Locust_Files import run_locust

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
SECONDS = 1000

API_LOAD_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
locust_file_prefix = "Locust_Files"
PROJECT_DIR = os.path.dirname(API_LOAD_TEST_DIR)

STATS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Stats")
LOGS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Load_Logs")
PLAYBACK_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, locust_file_prefix + "/playback_locust.py")
API_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, locust_file_prefix + "/api_locust.py")
DUMMY_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, locust_file_prefix + "/master_locust.py")

LocustFilePaths = namedtuple('LoucstFilePaths', ["web_host", "api", "playback"])

locust_file_paths = LocustFilePaths(DUMMY_LOCUST_FILE, API_LOCUST_FILE, PLAYBACK_LOCUST_FILE)


# TODO: Make salt stack configuration for build out on machines


class LoadRunner:
    assumed_load_average_added = 1
    assumed_cpu_used = 7
    Stat_Interval = 2
    total_used_cpu_running_threshold = 9  # TODO Find actual threshold
    process_age_limit = 2  # TODO Find process age limit
    Succesful_Test_Start = {"message": "Swarming started", "success": True}
    Succesful_Test_Stop = {"message": "Test stopped", "success": True}
    Max_Connection_Time = 5
    CPU_Measure_Interval = .2
    Boot_Time_Delay = 2.5  # TODO Find actual timing
    Max_Process_Wait_Time = 5
    UI_Action_Delay = 2

    # API CONFIG
    master_host_info = ("0.0.0.0", 5557)
    web_ui_host_info = ("0.0.0.0", 8089)
    web_api_host_info = ("0.0.0.0", 5000)
    test_runner_communication_info = ("0.0.0.0", 8000)

    Current_Automated_Test_Msg = u"An automated test is currently running on this server - view it through the UI"
    Current_Custom_Test_Msg = u"A custom test is currently running on this server - view it through the UI"
    TEST_API_WRAPPER = None
    Extension = '/LoadServer'
    PERSISTANT_LOAD_RUNNER = None

    @classmethod
    def setup(cls, config, defualt_2_cores):
        """
        This Method sets up an instance of the load runner that can be accessed from the primary process to avoid
        problems with closure when the api_app is initilized. (It avoids closure by making all references to the class
        variable go to the same place) e
        :param config:
        :param defualt_2_cores:
        :return:
        """
        runner = LoadRunner(LoadRunner.master_host_info, LoadRunner.web_ui_host_info, config)
        runner.default_2_cores = defualt_2_cores
        LoadRunner.PERSISTANT_LOAD_RUNNER = runner

    @classmethod
    def teardown(cls):
        if not LoadRunner.PERSISTANT_LOAD_RUNNER:
            pass
        else:
            LoadRunner.PERSISTANT_LOAD_RUNNER.stop_tests()

    # This variable is to set the virtualenv for each
    # Environment_Set = False

    # TODO: make a method to ensure the class is not running any proccesses from last run
    # TODO: make sure children is not tainted by automated_test in background
    def __init__(self, master_host_info, web_ui_info, config):
        self.web_host = None
        self.process_pool = Pool(1)
        self.slaves = []
        self.master_host_info = master_host_info
        self.web_ui_host_info = web_ui_info
        self.config = config
        self.expected_slaves = 0
        # self.__set_virtual_env()
        self._default_2_cores = False
        self._last_write_acton = time.time()
        self._last_boot_time = time.time()
        self._users = -1
        self._hatch_rate = -1
        self.web_client = LocustUIClient(self.web_ui_host_info[0], self.web_ui_host_info[1])

    @property
    def users(self):
        value = self.web_client.users
        return value

    @property
    def state(self):
        value = self.web_client.state
        return value

    @property
    def last_write(self):
        return self._last_write_acton

    @last_write.setter
    def last_write(self, value):
        self._last_write_acton = time.time()

    @property
    def slaves_loaded(self):
        try:
            slaves_count = self.web_client.slave_count
            if self.expected_slaves is not slaves_count:
                raise SlaveInitilizationException("All of the slaves where not loaded correctly")
            else:
                return True
        except SlaveInitilizationException as e:
            return False

    @property
    def children(self):
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        return children

    @property
    def cores(self):
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

    ########################################################################################################################
    ##########################################  API COMMANDS  ##############################################################
    ########################################################################################################################

    def stop_tests(self):
        self._kill_test()

    def is_running(self):
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

    def run_distributed(self, rps, api_call_weight, env, node, version, min, max):
        # TODO find a way to distribute segemented test data when running
        pass

    def custom_playback_test(self, client, playback_route, quality, codecs, users=None, dvr=None, days_old=None,
                             stat_int=2):
        self.__raise_if_running()
        self.stop_tests()
        self._verify_playback_options(client, playback_route, quality, codecs, users, dvr, days_old, stat_int)
        options = self._get_playback_options(client, playback_route, quality, codecs, stat_int, users, dvr, days_old)
        self._run_multi_core(options, locust_file_paths.web_host, locust_file_paths.playback)

    def custom_api_test(self, api_info, env, node, max_request, stat_interval=None,
                        assume_tcp=False, bin_by_resp=False):
        self.__raise_if_running()
        self.stop_tests()
        self._verify_api_params(api_info, env, node, max_request, stat_interval, assume_tcp, bin_by_resp)
        file_prefix = "Custom API"
        options = self._get_api_options(api_info, env, node, max_request, stat_interval, assume_tcp, bin_by_resp)
        self._run_multi_core(options, locust_file_paths.web_host, locust_file_paths.api,
                             stats_file_name=file_prefix, stats_folder=STATS_FOLDER,
                             log_file_name=file_prefix, log_folder=LOGS_FOLDER,
                             log_level="ERROR")

    def custom_api_to_failure(self, api_call_weight, env, node, stat_interval=None):
        self.__raise_if_running()
        self.stop_tests()
        # Here are some constants of this test
        file_prefix = "Failure API"
        max_reqeust = False
        assume_tcp = False
        bin_by_resp = True
        self._verify_api_params(api_call_weight, env, node, max_reqeust, stat_interval, assume_tcp, bin_by_resp)

    def run_automated_test_case(self, setup_name, procedure_name):
        # TODO implement way to run benchmark test
        self.__raise_if_running()
        self.stop_tests()
        # way to verify setup and procedure name
        # way to get all information and format it into the _run_nulti_core method
        file_prefix = "Automated"
        self.automated_test = AutomatedTestCase(setup_name, procedure_name,
                                                self, LoadRunner.Stat_Interval)
        self.automated_test.run()

    def start_ramp_up(self, locust_count, hatch_rate, first_start=False):
        return self.web_client.start_ramp_up(locust_count, hatch_rate, first_start)


    def get_stats(self):
        return self.web_client.stats

    def reset_stats(self):
        return self.web_client.reset_stats()


    def stop_ui_test(self):
        self.web_client.stop_test()





    ########################################################################################################################
    ##########################################  Server Utility #############################################################
    ########################################################################################################################

    def __raise_if_running(self):
        test_running = self.is_running()
        if test_running:
            raise TestAlreadyRunning(LoadRunner.Current_Custom_Test_Msg)

    def _kill_test(self):
        self.process_pool.terminate()
        self.process_pool.join()




    def _get_pool_length(self, route, env, *args):
        pool_factory = RequestPoolFactory(self.config, 0, 0, 0, 0, None, [env])
        the_info = pool_factory.get_route_pool_and_ribbon(route, *args)
        if isinstance(the_info, dict):
            for item in the_info.values():
                return len(item.pool)
        else:
            return len(the_info)

    ########################################################################################################################
    ##########################################  OPTION FUNCS  ##############################################################
    ########################################################################################################################

    # These are options creation commands
    def _get_api_options(self, api_info, env, node, max_req, stat_interval,
                         assume_tcp, bin_by_resp_time, comp_idx=0, max_comp_idx=0):
        # TODO find easy way to set size for each api list we will be grabbing
        # 1. Iterate through each api route key.
        # if its a route then go get the max size and set the size key
        # in the api locust setup when the locust is grabbing it's data set reset the size to the current size
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

    def _get_locust_options(self, host, locust_file, log_level, log_file,
                             slave, expected_slaves=None, stats_file=None):
        from argparse import Namespace
        if expected_slaves:
            master = True
        else:
            master = False
        options = Namespace()
        options.host = host
        options.web_host = self.web_ui_host_info[0]
        options.port = self.web_ui_host_info[1]
        options.locustfile = locust_file
        options.csvfilebase = stats_file or False

        # Put the location the Master UI Web host is listening on
        options.master_host = self.master_host_info[0]
        options.master_port = self.master_host_info[1]
        options.master_bind_host = self.master_host_info[0]
        options.master_bind_port = self.master_host_info[1]

        # MASTER SLAVE OPTIONS
        options.expect_slaves = expected_slaves or False
        options.master = master
        options.slave = slave

        # LOGGING/Stats OPTIONS
        options.loglevel = log_level or "DEBUG"
        options.logfile = log_file or False

        # MISC OPTIONS
        options.list_commands = False
        options.show_task_ratio = False
        options.show_task_ratio_json = False
        options.show_version = False
        options.reset_stats = False
        options.print_stats = False
        options.only_summary = False
        options.run_time = False
        options.no_web = False
        options.hatch_rate = False
        options.num_clients = False
        return options

    ########################################################################################################################
    ##########################################  FILEPATH FUNCS  ############################################################
    ########################################################################################################################

    # THESE ARE FILEPATH FUNCTIONS
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

    ########################################################################################################################
    ##########################################  Process Create  #############################################################
    ########################################################################################################################

    def _run_distributed(self, env_options, master_locust_file, slave_locust_file):
        pass

    # TODO: change back
    def _run_multi_core(self, env_options, master_locust_file, slave_locust_file,
                        stats_file_name=None, log_level=None, log_file_name=None,
                        reset_stats=False, stats_folder=None, log_folder=None):
        self._kill_test()
        # check current core loads to determine possible usage
        available_cores = self.cores
        if self.default_2_cores and available_cores < 2:
            available_cores = 2
        if available_cores <= 1:
            raise Load_Test.exceptions.NotEnoughAvailableCores(
                "There where only {cores} cores available for load test on this machine".format(
                    cores=available_cores))  # TO RUN MULTICORE WE NEED MORE THAN ONE CORE\
        # get all needed variables for slave/master options
        host = self.__get_host(env_options)
        self.expected_slaves = available_cores - 1
        stats_file_name, log_file_name = self.__get_file_paths(stats_folder, stats_file_name, log_folder, log_file_name)

        master_options = self._get_locust_options(host, master_locust_file, log_level, log_file_name, False,
                                                  self.expected_slaves, stats_file_name)
        slave_options = self._get_locust_options(host, slave_locust_file, log_level, log_file_name, True, None, stats_file_name)
        # configure all environment variables the locust may need
        env_options.max_slave_index = self.expected_slaves - 1
        env_options.stamp_env()
        locust_options = []
        # create the slave/master options
        locust_options.append((master_options, 0))
        for index in range(self.expected_slaves):
            locust_options.append((slave_options, index))
        # start the needed locust processes in multiprocessing pool and wait for web UI to load
        self._renew_pool(self.expected_slaves + 1)
        self.process_pool.map_async(run_locust, locust_options)
        self.__wait_till_loaded()


    def _run_single_core(self, env_options, locust_file, stats_file_name=None, log_level=None, log_file_name=None,
                         stats_folder=None, log_folder=None):
        self._kill_test()
        stats_file_name, log_file_name = self.__get_file_paths(stats_folder, stats_file_name, log_folder, log_file_name)
        host = self.__get_host(env_options)
        local_options = self._get_locust_options(host, locust_file, log_level, log_file_name, False, None, stats_file_name)
        self.expected_slaves = 0
        env_options.stamp_env()
        self._renew_pool(1)
        self.process_pool.apply_async(run_locust, [(local_options, 0)])
        self.__wait_till_loaded()


    def _renew_pool(self, process_count):
        def change_env():
            os.environ = os.environ.copy()
        self.process_pool = Pool(processes=process_count, initializer=change_env)


    ########################################################################################################################
    ##########################################  MISC HELPERS  ##############################################################
    ########################################################################################################################

    def _users_property_function_wrapper(self):
        return self.users


    def __get_host(self, options):
        if isinstance(options, APIWrap):
            host = self.config.get_api_host(options.env, options.node)
            return host
        elif isinstance(options, PlaybackWrap):
            host = self.config.get_api_host("DEV2", 0)
            return host

    ########################################################################################################################
    ##########################################  VERIFY FUNCS  ##############################################################
    ########################################################################################################################

    def _verify_playback_options(self, client, playback_route, quality, codecs, users, dvr, days_old,
                                 stat_int):  # check dist loc info

        # check playback route
        if playback_route not in self.config.playback_routes:
            raise InvalidPlaybackRoute("{rte} Invalid Playback Route - Valid: {vld}".format(rte=playback_route,
                                                                                            vld=str(
                                                                                                self.config.playback_routes)))
        # check playback client
        if client not in self.config.playback_players:
            raise InvalidPlaybackPlayer("{clt} Invalid Playback Player - Valid: {vld}".format(clt=client,
                                                                                              vld=str(
                                                                                                  self.config.playback_players)))
        # check plaback codec
        if not isinstance(codecs, list):
            if codecs and not isinstance(codecs[0], str):
                raise InvalidCodec("Invalid Playback Codec, codecs must be entered as list of strings")
        # check quality
        self.__verify_int("{} option".format(PlaybackWrap.QUALITY_KEY), quality)
        # check the stat_int
        self.__verify_int("{} option".format(PlaybackWrap.STAT_INT_KEY), stat_int)
        # Top N Playback is different than other routes
        if not playback_route == "Top N Playback":
            self.__verify_int("{} option".format(PlaybackWrap.USERS_KEY), users)
            self.__verify_int("{} option".format(PlaybackWrap.DVR_KEY), dvr)
            self.__verify_int("{} option".format(PlaybackWrap.DAYS_KEY), days_old)

    def _verify_api_params(self, api_call_weight, env, node, max_request, stat_interval, assume_tcp, bin_by_resp):
        # check dis locust
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
        # validate the route is an actual route
        for given_route in given_routes:
            if not self.config.is_route(given_route):
                raise InvalidRoute("{inv_route} is not a valid route".format(inv_route=given_route))
            route_params = api_call_weight[given_route]
            # validate the version is an actual version of the route
            for route_version in route_params.keys():
                if not self.config.is_version(given_route, int(route_version)):
                    raise InvalidAPIVersion("{version} is not a valid version for route {route}".format(
                        version=route_version, route=given_route
                    ))
                # verify the route contains all neccesary instance variables
                for neccesary_key in API_VERSION_KEYS:
                    if neccesary_key not in route_params[route_version].keys():
                        raise InvalidAPIVersionParams("{key} not in api_call {call} version {version}"
                                                      .format(key=neccesary_key, call=given_route,
                                                              version=route_version))

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

    ########################################################################################################################
    ##########################################  Server WAITS  ##############################################################
    ########################################################################################################################

    def __wait_till_loaded(self):
        retries = 0
        while True:
            our_state = self.state
            if our_state != "setup":
                if retries < 3:
                    retries =+ 1
                else:
                    raise ConnectionError("LOCUST UI WAS NOT ABLE TO OPEN")
            else:
                break


    def __post_action_wait(self):
        s_since = time.time() - self.last_write
        if s_since <= LoadRunner.UI_Action_Delay:
            to_sleep = LoadRunner.UI_Action_Delay - s_since
            time.sleep(to_sleep)

