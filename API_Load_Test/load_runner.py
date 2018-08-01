import datetime
import os
import psutil
import shlex
import subprocess as sp
import logging
import math
from api_exceptions import LoadRunnerFailedClose

from API_Load_Test.environment_wrapper import EnvironmentWrapper as EnvWrap
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
SECONDS = 1000


API_LOAD_TEST_DIR = os.path.dirname(os.path.abspath(__file__))


PROJECT_DIR = os.path.dirname(API_LOAD_TEST_DIR)
LOCALVENV_DIR = os.path.join(PROJECT_DIR, "localVenv")
VENV_DIR = os.path.join(PROJECT_DIR, "venv")


STATS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Stats")
LOGS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Logs")

SLAVE_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "api_locust.py")
MASTER_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "master_locust.py")
# TODO: Make salt stack configuration for build out on machines


class LoadRunner:
    assumed_load_average_added = 1
    assumed_cpu_used = 7
    cpu_samples = 5
    stat_interval = 2
    per_process_used_cpu_running_threshold = 5 #TODO Find actual threshold
    process_age_limit = 2 #TODO Find process age limit
#TODO: make a method to ensure the class is not running any proccesses from last run





    def __init__(self, master_host_info, web_ui_info, slave_locust_file, master_locust_file, config):
        self.master = None
        self.slaves = []
        self.master_locust_file = master_locust_file
        self.slave_locust_file = slave_locust_file
        self.master_host_info = master_host_info
        self.web_ui_host_info = web_ui_info
        self.config = config
        self.no_web = False
        self.expected_slaves = 0
        self.__set_virtual_env()




    def run_multi_core(self, api_call_weight, env, node, version, min, max,
                       stats_file_name=None, log_level=None, log_file_name=None, no_web=False,
                       reset_stats=False, num_clients=None, hatch_rate=None, run_time=None,
                       stats_folder=None, log_folder=None):


        self.no_web = no_web
        available_cores = self._avaliable_cpu_count()
        assert available_cores > 1  # TO RUN MULTICORE WE NEED MORE THAN ONE CORE

        self.expected_slaves = available_cores - 1
        os_env = self._get_configured_env(api_call_weight, env, version, node, min, max)
        stats_file_name, log_file_name = self._get_file_paths(stats_folder, stats_file_name, log_folder, log_file_name)

        master_options = self._create_master_options(env, node, stats_file_name, log_level, log_file_name, no_web, reset_stats,
                                                     self.expected_slaves, num_clients, hatch_rate, run_time)
        slave_options = self._create_slave_options(env, node, reset_stats)

        self.master = self._create_process(os_env.get_env(), master_options)

        to_be_slaves = []
        for index in range(self.expected_slaves):
            slave = self._create_process(os_env.get_env(), slave_options)
            to_be_slaves.append(slave)
        self.slaves = to_be_slaves


    def run_distributed(cls, rps, api_call_weight, env, node, version, min, max):
        pass

    def run_single_core(self, api_call_weight, env, node, version, min, max, stats_file_name=None, log_level=None, log_file_name=None,
                        no_web=False, reset_stats=False, num_clients=None, hatch_rate=None, run_time=None,
                        stats_folder=None, log_folder=None):

        self.no_web = no_web
        stats_file_name, log_file_name = self._get_file_paths(stats_folder, stats_file_name, log_folder, log_file_name)
        os_env = self._get_configured_env(api_call_weight, env, version, node, min, max)

        undis_options = self._create_undistributed_options(env, node, stats_file_name, log_level, log_file_name, no_web, reset_stats,
                                                           num_clients, hatch_rate, run_time)
        self.master = self._create_process(os_env.get_env(), undis_options)




    def test_currently_running(self):
        children = self.children
        if self.no_web is True and children:
            return True
        usage = 0
        for child in children:
            usage += child.cpu_percent(5)
        if usage/len(children) <= LoadRunner.per_process_used_cpu_running_threshold:
            self.stop_test()
            return False
        else:
            return True


    def stop_test(self):
        try:
            if self.no_web:
                info_list, return_codes = self._wait_till_done()
                self.__fresh_state()
                return info_list, return_codes
            else:
                self.__fresh_state()
                return 0
        except:
            raise





    def _wait_till_done(self):
        if self.master is None:
            self.__fresh_state()
            return None
        else:
            info_list = []
            info = self.master.communicate()
            info_list.append(info)
            return_codes = []
            return_codes.append(self.master.poll())
            for slave in self.slaves:
                info = slave.communicate()
                info_list.append(info)
                return_codes.append(slave.poll())
            return info_list, return_codes



    def __fresh_state(self):
        self._safe_kill(self.master)
        for slave in self.slaves:
           self._safe_kill(slave)
        self.master = None
        self.slaves = []
        if self._child_processes():
            raise LoadRunnerFailedClose("unsuccesfully closed all child proccesses")



    def _safe_kill(self, process):
        if process is None:
            return
        try:
            process.kill()
            process.wait()
        except OSError as e:
            if e.strerror == "No such process":
                pass
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
        percentage_per_cpu = 100/physical_cores
        idle_time_percentage = psutil.cpu_times_percent(LoadRunner.cpu_samples).idle - LoadRunner.assumed_cpu_used
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
        p = sp.Popen(options, env=os_env, stdout=sp.PIPE, stderr=sp.PIPE, stdin=sp.PIPE)
        return p



    def _get_configured_env(self, api_call_weight, env, version, node, normal_min, normal_max):
        my_env = EnvWrap(os.environ.copy(), API_CALL_WEIGHT=api_call_weight, VERSION=version,
                         NODE=node, ENV=env, N_MIN=normal_min, N_MAX=normal_max, STAT_INTERVAL=LoadRunner.stat_interval)
        return my_env


    def _create_master_options(self, env, node, csv_file=None, log_level=None, log_file=None, no_web=False,
                               reset_stats=False, expected_slaves=None, num_clients=None, hatch_rate=None, run_time=None):


        #TODO: Use the web_ui_host stuff eventually (when incorporating with DCMNGR)
        host = self.config.get_api_host(env, node)
        web_ui_host = self.web_ui_host_info[0]
        web_ui_port = self.web_ui_host_info[1]
        masterbindHost = self.master_host_info[0]
        masterbindPort = self.master_host_info[1]
        master_arg_string = "locust -f {master_file} -H {l_host} --master --master-bind-host={mb_host} --master-bind-port={mb_port}".format(
            master_file=self.master_locust_file, l_host=host, mb_host=masterbindHost, mb_port=masterbindPort
        )
        if csv_file is not None:
            master_arg_string = "{master_arg_string} --csv={file_name}".format(master_arg_string=master_arg_string, file_name=csv_file)
        if log_file is not None:
            master_arg_string = "{master_arg_string} --logfile={file_name}".format(master_arg_string=master_arg_string, file_name=log_file)
        if log_level is not None:
            master_arg_string = "{master_arg_string} --loglevel={loglevel}".format(master_arg_string=master_arg_string, loglevel=log_level)

        if no_web:
            assert expected_slaves is not None, "expected_slaves param required to run locust in no web state"
            assert num_clients is not None, "num_clients param required to run locust in no web state"
            assert hatch_rate is not None, "hatch_rate param required to run locust in no web state"
            assert run_time is not None, "run_time param required to run locust in no web state"
            assert csv_file is not None, "csv_file param required to run locust in no web state"
            master_arg_string = "{master_arg_string} --no-web -c {n_clients} -r {n_hatch} -t {n_time} --expect-slaves={e_slaves}".format(
                master_arg_string=master_arg_string, n_clients=num_clients, n_hatch=hatch_rate, n_time=run_time, e_slaves=expected_slaves
            )
            if reset_stats:
                master_arg_string = "{master_arg_string} --reset-stats".format(master_arg_string=master_arg_string)

        return shlex.split(master_arg_string)


    def _create_slave_options(self, env, node, reset_stats=False):
        host = self.config.get_api_host(env, node)
        masterhost = self.master_host_info[0]
        masterport = self.master_host_info[1]

        slave_arg_string = "locust -f {slave_file} -H {l_host} --slave --master-host={m_host} --master-port={m_port}".format(
            slave_file=self.slave_locust_file, l_host=host, m_host=masterhost, m_port=masterport
        )
        if reset_stats:
            slave_arg_string = "{slave_arg_string} --reset-stats".format(slave_arg_string=slave_arg_string)

        return shlex.split(slave_arg_string)



    def _create_undistributed_options(self, env, node, csv_file=None, log_level=None, log_file=None, no_web=False,
                               reset_stats=False, num_clients=None, hatch_rate=None, run_time=None):


        #TODO: Use the web_ui_host stuff eventually (when incorporating with DCMNGR)
        host = self.config.get_api_host(env, node)
        undis_arg_string = "locust -f {undis_file} -H {l_host} ".format(
            undis_file=self.slave_locust_file, l_host=host,
        )
        if csv_file is not None:
            undis_arg_string = "{undis_arg_string} --csv={file_name}".format(undis_arg_string=undis_arg_string, file_name=csv_file)
        if log_file is not None:
            undis_arg_string = "{undis_arg_string} --logfile={file_name}".format(undis_arg_string=undis_arg_string, file_name=log_file)
        if log_level is not None:
            undis_arg_string = "{undis_arg_string} --loglevel={loglevel}".format(undis_arg_string=undis_arg_string, loglevel=log_level)

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


    @property
    def master(self):
        return self._master


    @master.setter
    def master(self, value):
        if not self.children:
            raise LoadRunnerFailedClose("Overrding Master child process prior to closing it, this will result in zombie processes")
        if not isinstance(value, sp.Popen) and value is not None:
            raise ValueError("You cannot assign the master process a value that is not a subprocess or None")
        self._master = value


    @property
    def slaves(self):
        return self._slaves


    @slaves.setter
    def slaves(self, value):
        if not self.children:
            raise LoadRunnerFailedClose("Overriding Slave child processes prior to closing it, this will result in zombie processes")
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
                raise LoadRunnerFailedClose("You can not change the web status of a test without closing the previous test")

    @property
    def children(self):
        return self._child_processes()













