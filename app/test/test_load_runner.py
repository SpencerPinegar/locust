import math
import time

from app.Utils.route_relations import APIRoutesRelation as APIRel, PlaybackRoutesRelation as PlaybackRel
from app.Utils.locust_test import LocustTest
from app.Core.exceptions import TestAlreadyRunning


class TestLoadRunnerAPI(LocustTest):

    def setUp(self):
        super(TestLoadRunnerAPI, self).setUp()
        self.load_runner.default_2_cores = True


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
        stats = self.load_runner.get_stats()
        requests = stats["num requests"]
        self.assertTrue(True)

    def test_run_basic_automated_test_case(self):
        setup, procedure = ("Node User Recordings", "Test Basic")
        self._setup_and_start_automated_test(setup, procedure)

    # def test_run_multi_stage_automated_test_case(self):
    #     setup, procedure = ("Node User Recordings", "Test Level Platue Level Back Down")
    #     self._setup_and_start_automated_test(setup, procedure)

    # TODO: FINISH

########################################################################################################################
##########################################  HELPER FUNCS  ##############################################################
########################################################################################################################


    def _setup_and_start_custom_api_test(self, api_call=None, max_request=False):
        if api_call is None:
            api_call = self.api_call
        self.load_runner.custom_api_test(api_call, self.env, self.node, max_request, 2)
        self.load_runner.start_ramp_up(self.n_clients, self.hatch_rate)
        time.sleep(5)

    def _setup_and_start_automated_test(self, setup=None, procedure=None):
        setup = self.setup_name if setup is None else setup
        procedure = self.procedure_name if procedure is None else procedure
        self.load_runner.run_automated_test_case(setup, procedure)
        test_proc = self.config.get_test_procedure(procedure)
        time_for_test = 0
        for test in test_proc:
            try:
                hatch_time = (test["final user count"] - test["init user count"]) / test["hatch rate"]
            except ZeroDivisionError:
                hatch_time = 0
            time_for_test += int(test["time at load"]) + hatch_time
        time.sleep(5)

    def _kill_test(self):
        self.load_runner.stop_tests()

    def _assert_setup(self):
        is_setup = self.load_runner.state
        self.assertEqual("setup", is_setup,
                         "The test did not setup correctly")

    def _assert_running(self):
        is_running = self.load_runner.is_running()
        self.assertEqual(True, is_running, "The test did not start correctly")

    def _assert_not_setup(self):
        the_state = self.load_runner.state
        self.assertNotEqual("setup", the_state, "The test threads where not killed properly")

    def _assert_not_running(self):
        is_running = self.load_runner.is_running()
        self.assertEqual(False, is_running, "The test was not ended killed properly and is still running")

    def _assert_wont_start_while_running(self):
        with self.assertRaises(TestAlreadyRunning):
            self._setup_and_start_custom_api_test()
        with self.assertRaises(TestAlreadyRunning):
            self._setup_and_start_automated_test()

    def _assert_automated_test_file(self, file):
        # TODO: create this function
        pass


class TestLoadRunnerUnderTheHood(LocustTest):
    """
    These Tests are dependnet on the test_api_locust suit -- especially the test_user_recordigns_ribbon_route tests
    """

    def test_run_single_core_api(self):
        self._test_undistributed_api(APIRel.USER_RECORDING_RIBBON, False)

    def test_run_multi_core_api(self):
        self._test_multi_core_undistributed_api(APIRel.USER_RECORDING_RIBBON, False)

    def test_run_single_core_api_max_request(self):
        self._test_undistributed_api(APIRel.USER_RECORDING_RIBBON, True)

    def test_run_multi_core_api_max_request(self):
        self._test_multi_core_undistributed_api(APIRel.USER_RECORDING_RIBBON, True)

    def test_run_multi_core_api_assume_tcp(self):
        self._test_multi_core_undistributed_api(APIRel.USER_RECORDING_RIBBON, False, True)

    def test_run_multi_core_api_bin_by_resp(self):
        self._test_multi_core_undistributed_api(APIRel.USER_RECORDING_RIBBON, False, False, True)

    def test_run_single_core_playback(self):
        self._test_undistributed_playback(PlaybackRel.Top_N_Playback, "HLS", 0)

    def test_run_multi_core_playback(self):
        self._test_multi_core_undistributed_playback(PlaybackRel.Top_N_Playback, "HLS", 0)

    def test_grab_ui_request_distribution_stats(self):
        self._basic_setup()
        request_info_df = self.load_runner.web_client._get_ui_request_distribution_stats()
        requests = request_info_df["Total"]["num requests"]
        self.assertNotEqual(requests, 0, "No requests where sent out")

    def test_grab_ui_exception_info(self):
        self._basic_setup()
        request_info_df = self.load_runner.web_client._get_ui_exception_info()
        #kind of hacky but if no exception is thrown we know we got exception info
        info = request_info_df["Count"].tail(1) #this will exist if we got the correct resposne back
        self.assertTrue(True)

    def test_ui_info(self):
        self._basic_setup()
        info = self.load_runner.web_client._get_ui_info()
        self.assertTrue(True)

    def test_reset_stats(self):
        self._basic_setup()
        stats_file_before_reset = self.load_runner.web_client._get_ui_request_distribution_stats()
        self.load_runner.reset_stats()
        stats_file_after_reset = self.load_runner.web_client._get_ui_request_distribution_stats()
        pre_stats = stats_file_before_reset["Total"]["num requests"]
        post_stats = stats_file_after_reset["Total"]["num requests"]
        self.assertNotEqual(pre_stats, 0, "No requests where sent out")
        self.assertGreater(pre_stats, post_stats, "You did not correctly reset the stats through the ui")

    def test_stop_ui_test(self):
        self._basic_setup()
        self.load_runner.stop_ui_test()
        time.sleep(3)
        state = self.load_runner.state
        self.assertEqual("setup", state, "The Locust UI was not stopped correctly")

    def test_start_ui_load(self):
        users, hatchrate = (100, 40)
        self._basic_setup()
        self._assert_adjust_test(users, hatchrate)

    def test_multi_stage_load(self):
        user_1, hatchrate_1 = (200, 60)
        user_2, hatchrate_2 = (150, 60)
        user_3, hatchrate_3 = (200, 25)
        self._basic_setup()
        self._assert_adjust_test(user_1, hatchrate_1)
        self._assert_adjust_test(user_2, hatchrate_2)
        self._assert_adjust_test(user_3, hatchrate_3)



########################################################################################################################
##########################################  HELPER FUNCS  ##############################################################
########################################################################################################################


    def _basic_setup(self):
        self._test_undistributed_api("User Recordings Ribbon", False)

    def _assert_adjust_test(self, users, hatchrate):
        self.load_runner.start_ramp_up(users, hatchrate)
        self.__wait_hatched(users, hatchrate)
        actt_users = self.__user_amount()
        state_hopefully_running = self.load_runner.state
        self.assertEqual(users, actt_users, "All the users did not load properly")
        self.assertEqual("running", state_hopefully_running, "The Locust UI was not started correctly from UI")

    def __user_amount(self):
        data = self.load_runner.web_client._get_ui_info()
        return data["user_count"]

    def __wait_hatched(self, users, hatch_rate):
        time.sleep(math.ceil(users/hatch_rate))






