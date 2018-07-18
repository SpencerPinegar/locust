import os
from unittest import TestCase

import pandas

from Load_Test.api_locust import run_programmatically

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
test_stats_folder = os.path.join(PARENT_DIR, "test_stats/")

class TestAPILocust(TestCase):

    def setUp(self):
        for file in os.listdir(test_stats_folder):
            os.remove(os.path.join(test_stats_folder, file))
        assert len(os.listdir(test_stats_folder)) == 0


    def run_load_route(self, route, version):
        try:
            api_call_weight, env, node, normal_min, normal_max, runtime = ({route: 1},  "DEV2", 1, 5, 30, "10s")
            run_programmatically(api_call_weight, env, node, version, normal_min, normal_max, 12, 11, runtime
                                 , csvfilebase=test_stats_folder)
        except SystemExit:
            self.assertSetEqual(set(os.listdir(test_stats_folder)), {"_distribution.csv", "_requests.csv"}, "Locust was not able to create the neccesary statistics files")
            requests_file = pandas.read_csv(os.path.join(test_stats_folder, '_requests.csv'), delimiter=',', quotechar='"', index_col=False)
            self.assertEqual(requests_file["# failures"][1], 0, "There were more than 0 failures")
            self.assertGreater(requests_file["# requests"][1], 1000, "There were not enough requests sent out")


    def test_user_recordings_ribbon_route_load_v1(self):
        self.run_load_route("User Recordings Ribbon", 1)



    def test_user_franchise_ribbon_route_load_v1(self):
        self.run_load_route("User Franchise Ribbon", 1)


    def test_user_recspace_information_route_load_v1(self):
        self.run_load_route("User Recspace Information", 1)

    def test_update_user_settings_route_load_v1(self):
        self.run_load_route("Update User Settings", 1)

    #TODO: Update tests to include Create/Delete Recordings and user rules


    def test_protect_recordings_route_load_v1(self):
        self.run_load_route("Protect Recordings", 1)

    def test_mark_watched_v1(self):
        self.run_load_route("Mark Watched", 1)

    def test_update_rules_v1(self):
        self.run_load_route("Update Rules", 1)

    def test_list_rules_v1(self):
        self.run_load_route("List Rules", 1)









