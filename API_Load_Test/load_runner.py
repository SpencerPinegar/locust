import datetime
import math
import os
import psutil
import shlex
import subprocess as sp
import logging

from API_Load_Test.environment_wrapper import EnvironmentWrapper as EnvWrap
from API_Load_Test.Config.config import Config
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
SECONDS = 1000


API_LOAD_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Stats")
LOGS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Logs")

SLAVE_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "api_locust.py")
MASTER_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "master_locust.py")
# TODO: Make salt stack configuration for build out on machines


class LoadRunner:
    assumed_concurrency_percentage_consumed = 3
    cpu_samples = 5
    stat_interval = 2



    def __init__(self, master_host_info, web_ui_info, slave_locust_file, master_locust_file):
        self.master = None
        self.slaves = []
        self.master_locust_file = master_locust_file
        self.slave_locust_file = slave_locust_file
        self.master_host_info = master_host_info
        self.web_ui_host_info = web_ui_info
        self.config = Config()
        self.no_web = False
        self.expected_slaves = 0



    def run_multi_core(self, api_call_weight, env, node, version, min, max,
                       stats_file_name=None, log_level=None, log_file_name=None, no_web=False,
                       reset_stats=False, num_clients=None, hatch_rate=None, run_time=None,
                       stats_folder=None, log_folder=None):

        # TODO: make rps have an influence on the number of expected slaves/clients so it is within the expected range

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
        for index in range(self.expected_slaves):
            slave = self._create_process(os_env.get_env(), slave_options)
            self.slaves.append(slave)


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
        #TODO: make function that puts runner in clean state

        self.master = self._create_process(os_env.get_env(), undis_options)




    def close(self):
        if self.no_web:
            return self._wait_till_done()
        #TODO: find way to check status of web_ui locust and return -- returning zero for now
        else:
            self.__fresh_state()
            return 0





    def _wait_till_done(self):
        if self.master is None:
            self.__fresh_state()
            return None
        else:
            info = self.master.communicate()
            return_codes = []
            return_codes.append(self.master.poll())
            for slave in self.slaves:
                return_codes.append(slave.poll())
            self.__fresh_state()
            return max(return_codes)



    def __fresh_state(self):
        self._safe_kill(self.master)
        for slave in self.slaves:
           self._safe_kill(slave)
        self.master = None
        self.slaves = []


    def _safe_kill(self, process):
        if process is None:
            return
        try:
            process.kill()
        except OSError as e:
            if e.strerror == "No such process":
                pass
            else:
                raise e



    def _avaliable_cpu_count(cls):
        """
        Takes samples of the system CPU usage to determine how many CPU's must be allocated to current system priceless
        Returns the amount of available physical CPU's that can be used for load testing
        :return:
        """
        # TODO: Make this number change based on cpu usage, avgLoad, etc:
        physical_cores = psutil.cpu_count(
            logical=False)  # Get the # of hardware cores -- HyperThreading wont make a difference
        available_cores = math.floor(physical_cores * .6)
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






if __name__ == "__main__":
    pass
# TODO: put easy entry
