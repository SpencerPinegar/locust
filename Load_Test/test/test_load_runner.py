from Load_Test.api_test import APITest
import math
import time


class TestLoadRunner(APITest):
    """
    These Tests are dependnet on the test_api_locust suit -- especially the test_user_recordigns_ribbon_route tests
    """




    def test_run_single_core_no_web(self):
        self._test_undistributed("User Recordings Ribbon", 1, False)


    def test_run_single_core_web(self):
        self._test_undistributed("User Recordings Ribbon", 1, True)


    def test_run_multi_core_no_web(self):
        self._test_multi_core("User Recordings Ribbon", 1, False)

    def test_run_multi_core_web(self):
        self._test_multi_core("User Recordings Ribbon", 1, True)


    def test_grab_ui_request_distribution_stats(self):
        self._basic_setup()
        request_info_df = self.load_runner._get_ui_request_distribution_stats()
        requests = request_info_df["Total"]["num requests"]
        self.assertNotEqual(requests, 0, "No requests where sent out")



    def test_grab_ui_exception_info(self):
        self._basic_setup()
        request_info_df = self.load_runner._get_ui_exception_info()
        #kind of hacky but if no exception is thrown we know we got exception info
        info = request_info_df["Count"].tail(1) #this will exist if we got the correct resposne back
        self.assertTrue(True)


    def test_ui_info(self):
        self._basic_setup()
        info = self.load_runner._get_ui_info()
        print("huh")


    def test_reset_stats(self):
        self._basic_setup()
        stats_file_before_reset = self.load_runner._get_ui_request_distribution_stats()
        self.load_runner._reset_stats()
        stats_file_after_reset = self.load_runner._get_ui_request_distribution_stats()
        pre_stats = stats_file_before_reset["# requests"].tail(1).values[0]
        post_stats = stats_file_after_reset["# requests"].tail(1).values[0]
        self.assertNotEqual(pre_stats, 0, "No requests where sent out")
        self.assertGreater(pre_stats, post_stats, "You did not correctly reset the stats through the ui")




    def test_stop_ui_test(self):
        self._basic_setup()
        self.load_runner._stop_ui_test()
        time.sleep(1)
        state = self.load_runner._ui_state()
        self.assertEqual("stopped", state, "The Locust UI was not stopped correctly")


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







    def _basic_setup(self):
        self._test_undistributed("User Recordings Ribbon", 1, True)
        time.sleep(3)

    def _assert_adjust_test(self, users, hatchrate):
        self.load_runner._start_ui_load(users, hatchrate)
        self.__wait_hatched(users, hatchrate)
        actt_users = self.__user_amount()
        state_hopefully_running = self.load_runner._ui_state()
        self.assertEqual(users, actt_users, "All the users did not load properly")
        self.assertEqual("running", state_hopefully_running, "The Locust UI was not started correctly from UI")

    def __user_amount(self):
        data = self.load_runner._get_ui_info()
        return data["user_count"]

    def __wait_hatched(self, users, hatch_rate):
        time.sleep(math.ceil(users/hatch_rate))






