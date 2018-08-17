from Load_Test.api_test import APITest
from Load_Test.api_locust import APITasks

class TestAPILocust(APITest):


    def test_user_recordings_ribbon_route_load_v1(self):
        self._test_undistributed("User Recordings Ribbon", 1, False)



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

    def test_do_nothing_cpu_used(self):
        self._test_undistributed("Nothing", 1, False, assert_results=False)

    def test_redundant_ts_segment(self):
        self._test_undistributed("Redundant Ts Segment", 1, False)

    def test_basic_network(self):
        self._test_undistributed("Basic Network", 1, False)

    def test_network_byte_size(self):
        self._test_undistributed("Network Byte Size", 1, False)

    def test_small_db(self):
        self._test_undistributed("Small Data Base", 1, False)

    def test_large_db(self):
        self._test_undistributed("Large Data Base", 1, False)




    def test_2_routes_one_zero_weight(self):
        api_call_weight = {"User Recordings Ribbon": 1, "User Franchise Ribbon": 0}
        self._test_undistributed("DOESNT MATTER", 1, False, api_call_weight=api_call_weight, test_time="1m")

    def test_2_routes_both_weight(self):
        api_call_weight = {"User Franchise Ribbon": 10, "User Recordings Ribbon": 10}
        self._test_undistributed("DOESNT MATTER", 1, False, api_call_weight=api_call_weight, test_time="1m")


    def test_set_tasks(self):
        api_call_weight = {"User Recordings Ribbon": 1, "User Franchise Ribbon": 1}
        APITasks.api_call_weight = api_call_weight
        APITasks._set_tasks()

        print("huh")







