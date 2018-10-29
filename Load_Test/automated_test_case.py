
from time import time, sleep
import threading
from Load_Test.Misc.recurring_event_thread import RecurringEventThread
import os
import csv
from requests.exceptions import ConnectionError
import datetime
from collections import namedtuple
from collections import namedtuple

FailedRoute = namedtuple("FailedRoute", ["route", "perc_98", "percent_under_sla"])





"""
Assumptions:
    1. Test Procedures always start with zero users (enforced in setter of AutomatedTestCase)
    2. Tests are always set up within the action list  
    3. If an automated test is told to run (it is #1 priority)
    4. This test is reliant upon a load_runner_API_wrapper 
     

Design Principles (reference assumption)
    - Wait until test has >= the initial users before reseting ramp up or stats(1)
    - Action list contains setup logic (see inital keyword in __build_procedure_action_helper (2)
    - telling an automated test to run results in a teardown and set up of the current load runner (3)
    - All actions from this test are performed on the API Wrapper load_runner variable (4)
    
"""


class AutomatedTestCase:
    #TODO: MAKE THESE COME FROM CONFIG
    SLA_ms_max_time = 150
    CONSECUTIVE_FAILED_SNAPSHOTS_TIL_FAIL = 3
    TO_FAILURE_PROCEDURE = "TO FAILURE"

    def __init__(self, setup_name, procedures_name, api_test_runner, stat_interval):
        """
        Runs an automated testcase based on the testsetup and testprocedures
        :param TestSetup: Test Setup class with all values
        :param TestProceudures: List of TestProcedure Classes
        """
        #TODO make automated test case run in thread so it can access process memory
        self.name = "{setup}: {procedure} - {date}".format(setup=setup_name, procedure=procedures_name,
                                                           date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.stat_interval = stat_interval
        self.setup_test_method = api_test_runner.custom_api_test
        self.teardown_test_method = api_test_runner.stop_tests
        self.get_stats_method = api_test_runner.get_stats
        self.ramp_up_method = api_test_runner.start_ramp_up
        self.reset_stats_method = api_test_runner.reset_stats
        self.number_of_users = api_test_runner._users_property_function_wrapper

        self.started_test_time = time()
        self.setup = AutomatedTestCase.TestSetup.from_file(api_test_runner.config, setup_name)
        self.procedures = AutomatedTestCase.TestProcedure.from_file(api_test_runner.config, procedures_name)
        self.current_procedure = None
        self.started_procedure_time = None
        self.current_procedure_number = 0
        self.old_stats = None

        if AutomatedTestCase.TO_FAILURE_PROCEDURE in procedures_name:
            self.sla_failure = True
            self.setup.max_reqeust = False
            self.setup.assume_tcp = False
            self.setup.bin_by_resp = False
            self.failed = False
        else:
            self.sla_failure = False
            self.failed = False
        self.consecutive_failed_snapshots = 0
        self.last_passed_snapshot = None




    def stats(self):
        old_stats = self.old_stats
        new_stats = self.get_stats_method()
        new_stats["proc time"] = time() - self.started_procedure_time
        new_stats["group"] = self.current_procedure.group_name
        new_stats["procedure num"] = self.current_procedure_number
        new_stats["name"] = self.name
        if self.sla_failure:
            self.__check_and_handle_failure(new_stats)


        if old_stats != None:
            pass
            #TODO decide if we want to only calculate stats for that time stamp
        return new_stats


    def __check_and_handle_failure(self, stats):
        if self.__highest_percentage_failure(stats):
            self.consecutive_failed_snapshots += 1
            if self.consecutive_failed_snapshots >= AutomatedTestCase.CONSECUTIVE_FAILED_SNAPSHOTS_TIL_FAIL:
                self.failed = True
        else:
            if self.consecutive_failed_snapshots is 0:
                self.last_passed_snapshot = stats
            self.consecutive_failed_snapshots = 0


    def __highest_percentage_failure(self, stats):
        failed_times = []
        for path, dist_times in stats["stats"]:
            p_98 = dist_times["98%"]
            if p_98 > AutomatedTestCase.SLA_ms_max_time:


                if dist_times["50%"] > AutomatedTestCase.SLA_ms_max_time:
                    failed_times.append(FailedRoute(path, p_98, "<50%"))
                elif dist_times["66%"] > AutomatedTestCase.SLA_ms_max_time:
                    failed_times.append(FailedRoute(path, p_98, "<34%"))
                elif dist_times["75%"] > AutomatedTestCase.SLA_ms_max_time:
                    failed_times.append(FailedRoute(path, p_98, "<25%"))
                elif dist_times["80%"] > AutomatedTestCase.SLA_ms_max_time:
                    failed_times.append(FailedRoute(path, p_98, "<20%"))
                elif dist_times["90%"] > AutomatedTestCase.SLA_ms_max_time:
                    failed_times.append(FailedRoute(path, p_98, "<10%"))
                else:
                    failed_times.append(FailedRoute(path, p_98, "<2%"))

                failed_times.append(FailedRoute)

        return failed_times

    @property
    def ramped_up(self):
        if int(self.number_of_users()) < int(self.current_procedure.final_users):
            return False
        else:
            return True






    def __handle_procedures(self):
        stat_retriever = RecurringEventThread(self.stat_interval, self.stats)
        self.__handle_procedure(stat_retriever, True)
        while self.procedures and not self.failed:
            self.__handle_procedure(stat_retriever, False)
        stat_retriever.stop()
        self.teardown_test_method()





    def __handle_procedure(self, stat_retriever, initial=False):
        self.current_procedure_number += 1
        self.current_procedure = self.procedures.pop(0)
        self.started_procedure_time = time()
        if not initial:
            if self.current_procedure.fresh_stats:
                self.old_stats = None
                self.reset_stats_method()
            assert int(self.number_of_users()) == int(self.current_procedure.init_users)
        self.ramp_up_method(self.current_procedure.final_users, self.current_procedure.hatch_rate, first_start=False)
        stat_retriever.start()
        if self.sla_failure:
            while not self.failed:
                sleep(self.stat_interval)

        else:
            sleep(self.current_procedure.hatch_time_s)
            while not self.ramped_up:
                sleep(.002)
            if self.current_procedure.segregate:
                self.old_stats = None
                self.reset_stats_method()
            sleep(self.current_procedure.time_period)



    @staticmethod
    def __dict_to_csv(scraped_values_dict, file_path):
        my_dict = scraped_values_dict
        with open(file_path, 'a') as f:
            w = csv.DictWriter(f, my_dict.keys())
            if f.tell() == 0:
                w.writeheader()
                w.writerow(my_dict)
            else:
                w.writerow(my_dict)


    def run(self):
        self.teardown_test_method()
        self.setup_test_method(self.setup.api_call, self.setup.env, self.setup.node, self.setup.max_reqeust)
        self.started_test_time = time()
        test_controller = threading.Thread(name='Background Test', target=self.__handle_procedures)
        test_controller.setDaemon(True)
        test_controller.start()
        return test_controller




        #TODO: create thread and then run self.handle_procedures





    class TestSetup:

        def __init__(self, api_call, env, node, max_request, assume_tcp, bin_by_resp):
            self.api_call = api_call #json
            self.env = env #string enum
            self.node = node #small int
            self.max_reqeust = max_request #bool
            self.assume_tcp = assume_tcp
            self.bin_by_resp = bin_by_resp


        @classmethod
        def from_file(cls, config, name):
            setup_data = config.get_test_setup(name)
            api_call = setup_data["api call"]
            env = setup_data["env"]
            node = setup_data["node"]
            max_request = False #setup_data["max_request"]
            assume_tcp  = False #setup_data["assume_tcp"]
            bin_by_resp = False #setup_data["bin_by_resp"]
            test_setup = AutomatedTestCase.TestSetup(api_call, env, node, max_request, assume_tcp, bin_by_resp)
            return test_setup


    class TestProcedure:
        Modes = ["ramp up", "hold"]
        Types = ["Light", "Benchmark", "Stress", "Failure", "Spike", "Endurance"]

        def __init__(self, group_name, init_users, final_users, hatch_rate, time_period_s, segregate, fresh_stats):
            self.group_name = group_name

            self.init_users = init_users
            self.final_users = final_users
            self.hatch_rate = hatch_rate
            self.hatch_time_s = (final_users - init_users) / hatch_rate if final_users > init_users and hatch_rate > 0 else 0
            self.time_period = time_period_s
            self.segregate = segregate
            self.fresh_stats = fresh_stats




        @classmethod
        def from_file(cls, config, name):
            proc_data = config.get_test_procedure(name)
            proc_list = []
            for proc in proc_data:
                init_users = proc["init user count"]
                final_user_count = proc["final user count"]
                hatch_rate = proc["hatch rate"]
                time_period = float(proc["time at load"]) * 60
                fresh_stats = proc["fresh procedure stats"]
                segregate = proc["ramp up stats seperate"]
                test_proc = AutomatedTestCase.TestProcedure(name, init_users, final_user_count, hatch_rate, time_period, segregate,
                                                fresh_stats)
                proc_list.append(test_proc)
            return proc_list














