
from time import time, sleep
import threading
from Load_Test.recurring_event_thread import RecurringEventThread
import os
import csv
from requests.exceptions import ConnectionError





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
    API_Performance_Dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    Procedures_File = os.path.join(API_Performance_Dir, "Procedures.yaml")
    Setups_File = os.path.join(API_Performance_Dir, "Setups.yaml")

    def __init__(self, setup_name, procedures_name, stat_interval, setup_method, teardown_method, get_stats_method, ramp_up_method,
                 reset_stats_method, number_of_users_method, config):
        """
        Runs an automated testcase based on the testsetup and testprocedures
        :param TestSetup: Test Setup class with all values
        :param TestProceudures: List of TestProcedure Classes
        """
        #TODO make automated test case run in thread so it can access process memory
        self.stat_interval = stat_interval
        self.setup_test_method = setup_method
        self.teardown_test_method = teardown_method
        self.get_stats_method = get_stats_method
        self.ramp_up_method = ramp_up_method
        self.reset_stats_method = reset_stats_method
        self.number_of_users = number_of_users_method

        self.started_test_time = time()
        self.setup = AutomatedTestCase.TestSetup.from_file(config, setup_name)
        self.procedures = AutomatedTestCase.TestProcedure.from_file(config, procedures_name)
        self.current_procedure = None
        self.started_procedure_time = None
        self.current_procedure_number = 0
        self.stat_retriever = RecurringEventThread(stat_interval, self.__handle_stats)






    @property
    def ramped_up(self):
        print("LOLOLOL")
        print("lo,")
        print("lolol")
        print("lo,o,lolol")
        print("hey")
        if int(self.number_of_users()) < int(self.current_procedure.final_users):
            return False
        else:
            return True


    def __handle_procedures(self):
        self.__handle_procedure(True)
        while self.procedures:
            self.__handle_procedure(False)
        self.stat_retriever.stop()
        self.teardown_test_method()





    def __handle_procedure(self, initial=False):
        self.current_procedure_number += 1
        self.current_procedure = self.procedures.pop(0)
        self.started_procedure_time = time()
        if not initial:
            if self.current_procedure.fresh_stats:
                self.reset_stats_method()
            assert self.number_of_users == self.current_procedure.init_users
        self.ramp_up_method(self.current_procedure.final_users, self.current_procedure.hatch_rate)
        self.stat_retriever.start()
        sleep(self.current_procedure.hatch_time_s)
        while not self.ramped_up:
            sleep(.5)
        if self.current_procedure.segregate:
            self.reset_stats_method()
        sleep(self.current_procedure.time_period)


    def __handle_stats(self):
        stats = self.get_stats_method()
        proc_time = time() - self.started_procedure_time
        group = self.current_procedure.group_name
        stats["proc time"] = proc_time
        stats["group"] = group
        stats["procedure num"] = self.current_procedure_number
        file = os.path.join(AutomatedTestCase.API_Performance_Dir, "testerzzzzz")
        AutomatedTestCase.__dict_to_csv(stats, file)

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
        self.setup_test_method(self.setup.api_call, self.setup.env, self.setup.node, self.setup.version, self.setup.n_min,
                     self.setup.n_max)
        self.started_test_time = time()
        self.__handle_procedures()
        # test_controller = threading.Thread(name='Aut', target=self.__handle_procedures)
        # test_controller.setDaemon(True)
        # test_controller.start()





        #TODO: create thread and then run self.handle_procedures





    class TestSetup:

        def __init__(self, api_call, env, node, version, n_min, n_max):
            self.api_call = api_call
            self.env = env
            self.node = node
            self.version = version
            self.n_min = n_min
            self.n_max = n_max

        @classmethod
        def from_file(cls, config, name):
            setup_data = config.get_test_setup(name)
            api_call = setup_data["api call"]
            env = setup_data["env"]
            node = setup_data["node"]
            version = setup_data["version"]
            n_min = setup_data["min"]
            n_max = setup_data["max"]
            test_setup = AutomatedTestCase.TestSetup(api_call, env, node, version, n_min, n_max)
            return test_setup


    class TestProcedure:
        Modes = ["ramp up", "hold"]
        Types = ["Light", "Benchmark", "Stress", "Failure", "Spike", "Endurance"]

        def __init__(self, group_name, init_users, final_users, hatch_rate, time_period_s, segregate, fresh_stats):
            self.group_name = group_name

            self.init_users = init_users
            self.final_users = final_users
            self.hatch_rate = hatch_rate
            self.hatch_time_s = final_users - init_users / hatch_rate if final_users > init_users and hatch_rate > 0 else 0
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
                time_period = proc["time at load"]
                fresh_stats = proc["fresh procedure stats"]
                segregate = proc["ramp up stats seperate"]
                test_proc = AutomatedTestCase.TestProcedure(name, init_users, final_user_count, hatch_rate, time_period, segregate,
                                                fresh_stats)
                proc_list.append(test_proc)
            return proc_list














