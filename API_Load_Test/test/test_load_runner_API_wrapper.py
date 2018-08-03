from API_Load_Test.test.api_test import APITest
from API_Load_Test.load_runner_api_wrapper import LoadRunnerAPIWrapper
from API_Load_Test.exceptions import TestAlreadyRunning

class TestLoadRunnerAPIWrapper(APITest):

    def setUp(self):
        super(TestLoadRunnerAPIWrapper, self).setUp()
        self.load_runner_api_wrapper = LoadRunnerAPIWrapper(self.config, self.load_runner)
        self.load_runner_api_wrapper.test_runner.default_2_cores = True
        self._kill_test()

    def tearDown(self):
        self._kill_test()



    def test_not_setup_while_running(self):
        self._setup_and_start_benchmark_test()
        self._assert_not_setup()

    def test_no_web_initial(self):
        no_web = self.load_runner_api_wrapper.no_web
        self.assertEqual(None, no_web)

    def test_is_test_running_not_running(self):
        self._assert_not_setup()
        self._assert_not_running()

    def test_start_manuel_check_ui_page_dont_start_test_assert_not_running(self):
        self._setup_manual_test()
        self._assert_setup()
        self._assert_not_running()


    def test_start_manuel_start_test_assert_running_wont_start_another_test(self):
        self._setup_manual_test()
        self._assert_setup()
        self._start_manuel_test()
        self._assert_running()
        self._assert_wont_start_while_running()
        self._assert_running()


    def test_start_manuel_with_already_running_kill_then_start(self):
        self._setup_manual_test()
        self._assert_setup()
        self._start_manuel_test()
        self._assert_running()
        self._assert_wont_start_while_running()
        self._assert_running()
        self._kill_test()
        self._assert_not_setup()
        self._setup_manual_test()
        self._assert_setup()
        self._assert_not_running()
        self._start_manuel_test()
        self._assert_running()

    def test_start_benchmark_assert_setup_and_running(self):
        self._setup_and_start_benchmark_test()
        self._assert_running()

    def test_start_benchmark_test_assert_running_wont_start_another_test(self):
        self._setup_and_start_benchmark_test()
        self._assert_running()
        self._assert_wont_start_while_running()
        self._assert_running()

    def test_start_benchmark_test_assert_running_kill_then_start(self):
        self._setup_and_start_benchmark_test()
        self._assert_running()
        self._assert_wont_start_while_running()
        self._assert_running()
        self._kill_test()
        self._assert_not_setup()
        self._assert_not_running()
        self._setup_and_start_benchmark_test()
        self._assert_running()











    def _setup_manual_test(self):
        self.load_runner_api_wrapper.setup_manuel_test(self.api_call, self.env, self.node, self.version, self.n_min,
                                                       self.n_max)



    def _setup_and_start_benchmark_test(self):
        self.load_runner_api_wrapper.setup_and_start_benchmark_test(self.api_call, self.env, self.node, self.version, self.n_min,
                                                                    self.n_max, self.n_clients, self.hatch_rate, self.time, False)

    def _start_manuel_test(self):
        self.load_runner_api_wrapper.start_manuel_from_ui(locust_count=200, hatch_rate=200)

    def _kill_test(self):
        self.load_runner_api_wrapper.stop_tests()


    def _assert_setup(self):
        is_setup, verify_started_msg = self.load_runner_api_wrapper.is_setup()
        self.assertEqual(True, is_setup,
                         "The test did not setup correctly")


    def _assert_running(self):
        is_running, test_type = self.load_runner_api_wrapper.is_running()
        self.assertEqual(True, is_running, "The test did not start correctly")


    def _assert_not_setup(self):
        is_setup, verify_setup_msg = self.load_runner_api_wrapper.is_setup()
        self.assertEqual(False, is_setup, "The test threads where not killed properly")


    def _assert_not_running(self):
        is_running, running_msg = self.load_runner_api_wrapper.is_running()
        self.assertEqual(False, is_running, "The test was not ended killed properly and is still running")

    def _assert_wont_start_while_running(self):
        with self.assertRaises(TestAlreadyRunning):
            self._setup_manual_test()
        with self.assertRaises(TestAlreadyRunning):
            self._setup_and_start_benchmark_test()








