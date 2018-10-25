from Load_Test.Misc.locust_test import LocustTest
from Load_Test.load_runner_api_wrapper import LoadRunnerAPIWrapper
from Load_Test.exceptions import TestAlreadyRunning
import time
from Load_Test.Misc.utils import build_api_info

class TestLoadRunnerAPIWrapper(LocustTest):

    def setUp(self):
        super(TestLoadRunnerAPIWrapper, self).setUp()
        api_wrapper = LoadRunnerAPIWrapper(self.master_host_info, self.web_ui_host_info, self.config)
        api_wrapper.default_2_cores = True
        LoadRunnerAPIWrapper.TEST_API_WRAPPER = api_wrapper
        self.api_wrapper = api_wrapper
        self._kill_test()

        self.procedure_name = "Proc name"
        self.setup_name     = "setup name"

    def tearDown(self):
        self._kill_test()



    def test_not_setup_while_running(self):
        self._setup_and_start_custom_api_test()
        self._assert_not_setup()


    def test_is_test_running_not_running(self):
        self._assert_not_setup()
        self._assert_not_running()

    def test_start_custom_check_ui_page_assert_running(self):
        self._setup_and_start_custom_api_test()
        self._assert_running()


    def test_start_custom_start_test_assert_running_wont_start_another_test(self):
        self._setup_and_start_custom_api_test()
        self._assert_running()
        self._assert_wont_start_while_running()
        self._assert_running()


    def test_start_custom_with_already_running_kill_then_start(self):
        self._setup_and_start_custom_api_test()
        self._assert_running()
        self._assert_wont_start_while_running()
        self._assert_running()
        self._kill_test()
        self._assert_not_setup()
        self._setup_and_start_custom_api_test()
        self._assert_running()

    def test_start_automated_assert_setup_and_running(self):
        self._setup_and_start_automated_test()
        self._assert_running()

    def test_start_automated_test_assert_running_wont_start_another_test(self):
        self._setup_and_start_automated_test()
        self._assert_running()
        self._assert_wont_start_while_running()
        self._assert_running()

    def test_start_automated_test_assert_running_kill_then_start(self):
        self._setup_and_start_automated_test()
        self._assert_running()
        self._assert_wont_start_while_running()
        self._assert_running()
        self._kill_test()
        self._assert_not_setup()
        self._assert_not_running()
        self._setup_and_start_automated_test()
        self._assert_running()



    def test_test_route_as_api_route(self):

        self._setup_and_start_custom_api_test(self.test_api_call)
        self._assert_running()
        self._kill_test()



    def test_get_stats(self):
        self._setup_and_start_custom_api_test()
        stats = self.api_wrapper .get_stats()
        requests = stats["num requests"]
        self.assertTrue(True)

    def test_run_basic_automated_test_case(self):
        setup, procedure = ("Node User Recordings", "Test Basic")
        self._setup_and_start_automated_test(setup, procedure)

    def test_run_multi_stage_automated_test_case(self):
        setup, procedure = ("Node User Recordings", "Test Level Platue Level Back Down")
        self._setup_and_start_automated_test(setup, procedure)

    #TODO: FINISH

    def _setup_and_start_custom_api_test(self, api_call=None, max_request=False):
        if api_call is None:
            api_call = self.api_call
        self.api_wrapper.custom_api_test(api_call, self.env, self.node, max_request, 2)
        #self.api_wrapper.start_ramp_up(self.n_clients, self.hatch_rate)

    def _setup_and_start_automated_test(self, setup=None, procedure=None):
        setup = self.setup_name if setup is None else setup
        procedure = self.procedure_name if procedure is None else procedure
        self.api_wrapper.run_automated_test_case(setup, procedure)
        test_proc = self.config.get_test_procedure(procedure)
        time_for_test = 0
        for test in test_proc:
            hatch_time = (test["final user count"] - test["init user count"])/test["hatch rate"]
            time_for_test += int(test["time at load"]) + hatch_time
        time.sleep(1.2 * time_for_test)

    def _kill_test(self):
        self.api_wrapper.stop_tests()


    def _assert_setup(self):
        is_setup = self.api_wrapper.state
        self.assertEqual("setup", is_setup,
                         "The test did not setup correctly")


    def _assert_running(self):
        is_running = self.api_wrapper.is_running()
        self.assertEqual(True, is_running, "The test did not start correctly")


    def _assert_not_setup(self):
        the_state = self.api_wrapper.state
        self.assertNotEqual("setup", the_state, "The test threads where not killed properly")


    def _assert_not_running(self):
        is_running = self.api_wrapper.is_running()
        self.assertEqual(False, is_running, "The test was not ended killed properly and is still running")

    def _assert_wont_start_while_running(self):
        with self.assertRaises(TestAlreadyRunning):
            self._setup_and_start_custom_api_test()
        with self.assertRaises(TestAlreadyRunning):
            self._setup_and_start_automated_test()



    def _assert_automated_test_file(self, file):
        #TODO: create this function
        pass









