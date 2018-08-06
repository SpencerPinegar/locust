from Load_Test.test.api_test import APITest


class TestAPILocust(APITest):


    def test_user_recordings_ribbon_route_load_v1(self):
        self._test_undistributed("User Recordings ribbon", 1, True)



    def test_user_franchise_ribbon_route_load_v1(self):
        self._test_undistributed("User Franchise Ribbon", 1, False)


    def test_user_recspace_information_route_load_v1(self):
        self._test_undistributed("User Recspace Information", 1, False)

    def test_update_user_settings_route_load_v1(self):
        self._test_undistributed("Update User Settings", 1, False)

    #TODO: Update tests to include Create/Delete Recordings and user rules


    def test_protect_recordings_route_load_v1(self):
        self._test_undistributed("Protect Recordings", 1, False)

    def test_mark_watched_v1(self):
        self._test_undistributed("Mark Watched", 1, False)

    def test_update_rules_v1(self):
        self._test_undistributed("Update Rules", 1, False)

    def test_list_rules_v1(self):
        self._test_undistributed("List Rules", 1, False)




    def test_redundant_ts_segment(self):
        self._test_undistributed("Redundant Ts Segment", 1, True)

    def test_do_nothing_cpu_used(self):
        self._test_undistributed("Nothing", 1, False, assert_results=False)









