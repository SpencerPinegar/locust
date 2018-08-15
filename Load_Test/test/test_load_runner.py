from Load_Test.api_test import APITest
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


    def test_grab_ui_request_info_stats(self):
        self._test_undistributed("User Recordings Ribbon", 1, True)
        time.sleep(3)
        request_info_df = self.load_runner.grab_ui_request_info_stats()
        self.assertEqual(request_info_df["# failures"].tail(1).values[0], 0, "There were more than 0 failures")
        self.assertNotEqual(request_info_df["# requests"].tail(1).values[0], 0, "No requests where sent out")



    def test_grab_ui_request_distribution_stats(self):
        self._test_undistributed("User Recordings Ribbon", 1, True)
        time.sleep(3)
        request_info_df = self.load_runner.grab_ui_request_distribution_stats()
        self.assertNotEqual(request_info_df["# requests"].tail(1).values[0], 0, "No requests where sent out")



    def test_grab_ui_exception_info(self):
        self._test_undistributed("User Recordings Ribbon", 1, True)
        time.sleep(3)
        request_info_df = self.load_runner.grab_ui_exception_info()
        #kind of hacky but if no exception is thrown we know we got exception info
        info = request_info_df["Count"].tail(1) #this will exist if we got the correct resposne back
        self.assertTrue(True)










