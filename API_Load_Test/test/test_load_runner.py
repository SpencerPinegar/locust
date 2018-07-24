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

        #connection options
        self.version = 4
        self.node = 0 #node 0 is the VIP
        self.env = "DEV2"


        #test options
        self.api_call = {"User Recordings Ribbon": 1}
        self.n_min = 5
        self.n_max = 30


        #web options
        self.web_host = "localhost"
        self.no_web = False
        self.n_clients = 2000
        self.hatch_rate = .5
        self.time = "30s"
        self.exp_slaves = 16




    def test_available_cpu_count(self):
        self.assertTrue(0 < self.runner._avaliable_cpu_count() < psutil.cpu_count(logical=False))

    def test_run_slave(self):
        try:
            load_runner.LoadRunner._run_slave(api_call_weight=self.api_call, env=self.env, version=self.version,
                                              min=self.n_min, max=self.n_max, no_web=self.no_web, node=self.node)
        except SystemExit as e:
            self.assertEqual(e.args[0], 0)

    def test_run_master(self):
        try:
            kwargs = {}
            if self.no_web:
                kwargs = {"num_clients": self.n_clients, "hatch_rate":self.hatch_rate, "run_time":self.time}

            load_runner.LoadRunner._run_master(expected_slaves=self.exp_slaves, no_web=self.no_web, node=self.node,
                                               web_host=self.web_host, **kwargs)

        except SystemExit as e:
            self.assertEqual(e.args[0], 0)

    def test_run_multi_core(self):
        api_call_weight, version, env, node, normal_min, normal_max, runtime = ({"User Recordings Ribbon": 1}, 1, "DEV2", 1, 5, 30, "45s")
        try:
            self.runner.run_multi_core(runtime, "Doesnt matter RN", api_call_weight, env, node, version, normal_min, normal_max, stats_file_name="test")
        except SystemExit as e:
            self.assertEqual(e.args[0], 0)


