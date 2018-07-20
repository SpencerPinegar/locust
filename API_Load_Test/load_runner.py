import datetime
import math
import os

import psutil
import shlex
import subprocess as sp
from API_Load_Test.Config.config import Config
from API_Load_Test.request_pool import RequestPoolFactory
from api_locust import APITasks, APIUser, MasterUser
from locust import create_options, run_locust

API_LOAD_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FOLDER = os.path.join(API_LOAD_TEST_DIR, "Stats")

# TODO: Make salt stack configuration for build out on machines




class LoadRunner:
    assumed_concurrency_percentage_consumed = 3
    cpu_samples = 5



    @classmethod
    def run_multi_core(cls, run_time, rps, api_call_weight, env, node, version, min, max, print_stats = False,
                       stats_file_name = None, reset_stats=False):


        # TODO: make rps have an influence on the number of expected slaves/clients so it is within the expected range
        available_cores = cls._avaliable_cpu_count()
        assert available_cores > 1  # TO RUN MULTICORE WE NEED MORE THAN ONE CORE
        expected_slaves = available_cores - 1
        master_params = {
            "run_time": run_time,
            "reset_stats": reset_stats,
            "expected_slaves": expected_slaves,
            "num_clients": 14,
            "hatchrate": 7,
            "node": node,
            "env": env,
            "print_stats": print_stats
        }
        slave_params = {
                     "api_call_weight": api_call_weight,
                     "env": env,
                     "version": version,
                     "min": min,
                     "max": max,
                     "reset_stats": reset_stats
        }
        if stats_file_name is not None:
            stats_file_path = cls._get_file_path_in_todays_folder(stats_file_name)
            master_params.setdefault("csvfilebase", stats_file_path)

        master_info = [LoadRunner._run_master, master_params]
        slave_info = [LoadRunner._run_slave, slave_params]
        thread_data = []
        for slaves in range(expected_slaves):
            thread_data.append(slave_info)
        thread_data.insert(0, master_info)
        #pool = mp.Pool(processes=available_cores)
        #results = pool.map(LoadRunner._quick_map_, thread_data)
        #pool.close()
        #pool.join()


    @classmethod
    def run_distributed(cls, rps, api_call_weight, env, node, version, min, max):
        pass

    @classmethod
    def run_single_core(cls, api_call_weight, env, node, version, min, max, num_clients, hatchrate, runtime, **kwargs):
        # Set up local
        config = Config()
        pool_factory = RequestPoolFactory(config)
        host = config.get_api_host(env, node)
        APITasks.init_data(api_call_weight, pool_factory, version, env, min, max)
        APITasks.set_tasks(api_call_weight)
        options = create_options(locust_classes=[APIUser], host=host, no_web=True, num_clients=num_clients,
                                 hatch_rate=hatchrate, skip_log_setup=True, loglevel="DEBUG", run_time=runtime,
                                 **kwargs)
        run_locust(options)

    @staticmethod
    def _run_slave(api_call_weight={}, env="DEV2", version=1, min=0, max=None, no_web=True,
                   reset_stats=False, master_info=("127.0.0.1", 5557), **kwargs):
        # TODO: find way to distribute the init_data function between locusts on data sensitive info
        config = Config()
        pool_factory = RequestPoolFactory(config)
        master_host = master_info[0]
        master_port = master_info[1]
        APITasks.init_data(api_call_weight, pool_factory, version, env, min, max)
        APITasks.set_tasks(api_call_weight)
        options = create_options(locust_classes=[APIUser], no_web=no_web, reset_stats=reset_stats,
                                 skip_log_setup=True, loglevel="DEBUG",
                                 slave=True, master=False, master_host=master_host, master_port=master_port, **kwargs)
        run_locust(options)

    @staticmethod
    def _run_master(expected_slaves, env="DEV2", node=1, no_web=True,reset_stats=False, master_info=("127.0.0.1", 5557), **kwargs):
        config = Config()
        host = config.get_api_host(env, node)
        master_host = master_info[0]
        master_port = master_info[1]
        options = create_options(locust_classes=[MasterUser], no_web=no_web, skip_log_setup=True, loglevel="DEBUG",
                                 master=True, master_bind_host=master_host, expect_slaves=expected_slaves,
                                 master_bind_port=master_port, reset_stats=reset_stats, host=host,**kwargs)
        run_locust(options)

    @classmethod
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

    @staticmethod
    def _format_master_arg_string(options):
        return_val = shlex.split("locust -f locustfile.py --host the_host")
        args_string = " --host {h}"

    @classmethod
    def _get_file_path_in_todays_folder(cls, file_name):
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        todays_folder = os.path.join(STATS_FOLDER, today)
        file = os.path.join(todays_folder, file_name)
        if not os.path.exists(todays_folder):
            os.mkdir(todays_folder)
        return file



if __name__ == "__main__":
 pass
#TODO: put easy entry



