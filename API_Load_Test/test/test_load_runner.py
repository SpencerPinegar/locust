from unittest import TestCase
from API_Load_Test import load_runner
import psutil
import multiprocessing as mp
from collections import namedtuple

class TestLoadRunner(TestCase):
    """
    These Tests are dependnet on the test_api_locust suit -- especially the test_user_recordigns_ribbon_route tests
    """

    def setUp(self):
        self.runner = load_runner.LoadRunner()

    def test_available_cpu_count(self):
        self.assertTrue(0 < self.runner._avaliable_cpu_count() < psutil.cpu_count(logical=False))


    def test_run_slave(self):
        api_call_weight, version, env, normal_min, normal_max = ({"User Recordings Ribbon": 1}, 1, "DEV2", 5, 30)
        try:
            load_runner.LoadRunner._run_slave(api_call_weight=api_call_weight, env=env, version=version,
                                              min=normal_min, max=normal_max, no_web=False)
        except SystemExit as e:
            self.assertEqual(e.args[0], 0)

    def test_run_master(self):
        try:
            load_runner.LoadRunner._run_master(expected_slaves=4, no_web=False)#num_clients=2000, hatchrate=160, run_time="5m")
        except SystemExit as e:
            self.assertEqual(e.args[0], 0)

    def test_run_multi_core(self):
        api_call_weight, version, env, node, normal_min, normal_max, runtime = ({"User Recordings Ribbon": 1}, 1, "DEV2", 1, 5, 30, "45s")
        try:
            self.runner.run_multi_core(runtime, "Doesnt matter RN", api_call_weight, env, node, version, normal_min, normal_max, stats_file_name="test")
        except SystemExit as e:
            self.assertEqual(e.args[0], 0)


    def test____quick_map(self):
        load_runner.LoadRunner._format_arg_string("")

