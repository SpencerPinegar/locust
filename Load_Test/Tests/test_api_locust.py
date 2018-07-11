from Load_Test.Tests.api_test import APITest
from Load_Test.api_locust import run_programmatically
from sys import stdout, stderr


class TestAPILocust(APITest):



    def run_load_route(self, route):
        api_call_weight, version, env, node, normal_min, normal_max, runtime = ({route: 1}, 1, "DEV2", 1, 5, 30, "10s")
        run_programmatically(api_call_weight, env, node, version, normal_min, normal_max, 12, 11, runtime, skip_log_setup=True)
        self.assertTrue(True)

    def test_user_recordings_ribbon_route_load(self):

        self.run_load_route("User Recordings Ribbon")



        print("word")








