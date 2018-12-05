from app.Data.config import Config
from app.Utils.locust_test import LocustTest
import os

class TestPlaybackSettings(LocustTest):
    Expected_players = {"HLS", "DASH", "QMX"}
    Expected_playback_routes = {"Playback", "Top N Playback"}

    def setUp(self):
        LocustTest.setUp(self)

    def test_playback_routes(self):
        set_of_actual_routes = set(self.config.playback_routes)
        self.assertSetEqual(set(self.Expected_playback_routes), set_of_actual_routes, "Playback Routes broken")

    def test_playback_players(self):
        set_of_players = set(self.config.playback_players)
        self.assertSetEqual(self.Expected_players, set_of_players, "Playback Players broken")



class TestLoadRunnerSettings(LocustTest):

    Expected_rpc_port = 5000
    Expected_rpc_endpoint = "/LoadServer"
    Expected_locust_ui_port = 8089
    Expected_locust_ui_max_wait_time = 1
    Expected_locust_port = 5557
    Expected_SLA_cutoff = 150
    Expected_max_consecutive_frame = 3
    Expected_to_failure_prefix = "To Failure"
    Expected_stat_interval = 2
    Expected_preferred_master = "b-gp2-lgen-8.imovetv.com"
    Expected_potential_servers = ["b-gp2-lgen-8.imovetv.com", "b-gp2-lgen-9.imovetv.com"]

    def setUp(self):
        LocustTest.setUp(self)

    def test_rpc_port(self):
        self.assertTrue(self.Expected_rpc_port == self.config.rpc_port)

    def test_rpc_endpoints(self):
        self.assertTrue(self.Expected_rpc_endpoint == self.config.rpc_endpoint)


    def test_locust_ui_port(self):
       self.assertTrue(self.Expected_locust_ui_port == self.config.locust_ui_port)

    def test_locust_ui_max_wait(self):
        self.assertTrue(self.Expected_locust_ui_max_wait_time == self.config.locust_ui_max_wait)

    def test_locust_port(self):
        self.assertTrue(self.Expected_locust_port == self.config.locust_port)

    def test_response_time_cutoff_ms(self):
        self.assertTrue(self.Expected_SLA_cutoff == self.config.response_time_cutoff_ms)

    def test_to_failure_max_consecutive_failed_frames(self):
        self.assertTrue(self.Expected_max_consecutive_frame == self.config.to_failure_max_consecutive_failed_frames)

    def test_to_failure_procedure_prefix(self):
        self.assertTrue(self.Expected_to_failure_prefix == self.config.to_failure_procedure_prefix)

    def test_stat_reporting_interval(self):
        self.assertTrue(self.Expected_stat_interval == self.config.stat_reporting_interval)

    def test_preferred_master(self):
        self.assertTrue(self.Expected_preferred_master == self.config.preferred_master)

    def test_potential_servers(self):
        self.assertSetEqual(set(self.Expected_potential_servers), set(self.config.potential_servers))





class TestDatabaseSettings(LocustTest):
    Expected_database_base = {"Environments", "Credentials"}
    Expected_db_env = {"DEV1", "DEV2", "DEV3", "QA", "BETA", "BETA2"}
    Expected_db_env_params = {"Host", "Port"}
    Expected_credentials_set = {"DataBase Name", "DataBase Username", "DataBase Password"}


    def setUp(self):
        LocustTest.setUp(self)
        LocustTest.setUp(self)

    def test_build_settings_database_initial(self):
        try:

            actual_database_base = set(self.config._settings["DataBase Settings"].keys())
            self.assertSetEqual(self.Expected_database_base, actual_database_base)
        except Exception as e:
            self.fail(e)

    def test_build_settings_database_enviorments(self):
        try:

            actual_db_env = set(self.config._settings["DataBase Settings"]["Environments"])
            self.assertSetEqual(self.Expected_db_env, actual_db_env)
            for env in actual_db_env:
                actual_db_env_params = set(self.config._settings["DataBase Settings"]["Environments"][env])
                self.assertSetEqual(self.Expected_db_env_params, actual_db_env_params)
        except Exception as e:
            self.fail(e)

    def test_build_settings_database_credentials(self):
        try:

            actual_credentials_set = set(self.config._settings["DataBase Settings"]["Credentials"].keys())
            self.assertSetEqual(self.Expected_credentials_set, actual_credentials_set)
        except KeyError as e:
            self.fail("Could Not find key {0} in settings".format(e))

        except Exception as e:
            self.fail(e)

    def test_get_db_info(self):
        for env in self.Expected_db_env:
            env_info = self.config._settings["DataBase Settings"]["Environments"][env]
            expected_credentials = ("dvrcloud", "dvrcloud", "dvrcloud_pw", env_info["Host"], env_info["Port"])
            self.assertEqual(self.config._get_db_info(env), expected_credentials)

    def test_get_db_connection(self):
        for env in self.Expected_db_env:
            conn = self.config.get_db_connection(env)
            self.assertFalse(conn == None)



class TestRecAPIConfig(LocustTest):
    Expected_routes_params = {"Route", "Versions", "Normal Min", "Normal Max", "Version 1", "List"}
    Expected_api_env_params = {"VIP Host", "Node Host", "Total Nodes"}
    Expected_api_base = {"Environments", "Routes", "Misc Tests"}
    Expected_misc_tests = {"Nothing", "Redundant Ts Segment", "Basic Network", "Network Byte Size", "Small Db",
                                "Large Db"}
    Expected_setup_params = {"node", "version", "env", "min", "max", "api call"}
    Expected_procedure_params = {"init user count", "final user count", "hatch rate", "time at load",
                                      "fresh procedure stats", "ramp up stats seperate"}

    def setUp(self):
        LocustTest.setUp(self)

    def test_file_exists(self):
       self.assertTrue(os.path.exists(Config.SETTINGS_PATH))

    def test_recAPI_initial(self):
        try:

            actual_api_base = set(self.config._settings["RecAPI Settings"].keys())
            self.assertSetEqual(self.Expected_api_base, actual_api_base)
        except Exception as e:
            self.fail(e)

    def test_recAPI_enviorments(self):
        try:
            acutal_api_env = set(self.config._settings["RecAPI Settings"]["Environments"])
            self.assertSetEqual(self.expected_api_env, acutal_api_env)

            for env in acutal_api_env:
                acutal_api_env_params = set(self.config._settings["RecAPI Settings"]["Environments"][env].keys())
                self.assertSetEqual(self.Expected_api_env_params, acutal_api_env_params)
        except Exception as e:
            self.fail(e)

    def test_recAPI_routes(self):
        try:
            actual_routes = set(self.config._settings["RecAPI Settings"]["Routes"].keys())
            self.assertSetEqual(self.expected_routes, actual_routes)

            for route in actual_routes:
                actual_routes_params = set(self.config._settings["RecAPI Settings"]["Routes"][route].keys())
                for needed_param in self.Expected_routes_params:
                    self.assertTrue(actual_routes_params.__contains__(needed_param))
        except Exception as e:
            self.fail(e)

    def test_is_api_env(self):
        for env in self.expected_api_env:
            self.assertTrue(self.config.is_api_env(env))
        self.assertFalse(self.config.is_api_env("NOTAPIENV"))

    def test_is_node(self):
        for env in self.expected_api_env:
            max_node = self.config._quick_api_env[env]["Total Nodes"]
            min_node = 0
            self.assertTrue(self.config.is_node(env, max_node))
            self.assertTrue(self.config.is_node(env, min_node))
            self.assertTrue(self.config.is_node(env, max_node - 1))
            self.assertFalse(self.config.is_node(env, max_node + 1))
            self.assertFalse(self.config.is_node(env, min_node - 1))

    def test_is_route(self):
        for route in self.expected_routes:
            self.assertTrue(self.config.is_route(route))
        self.assertFalse(self.config.is_route("ISNOTROUTE"))

    def test_is_version(self):
        for route in self.expected_routes:
            info = self.config._get_route_info(route)
            for version in info["Versions"]:
                self.assertTrue(self.config.is_version(route, version))
                self.assertFalse(self.config.is_version(route, 0))

    def test_get_host(self):
        for env in self.expected_api_env:
            self.assertEqual(self.config._get_host(env, 0), self.config._quick_api_env[env]["VIP Host"])
            self.assertEqual(self.config._get_host(env, 1), self.config._quick_api_env[env]["Node Host"].format(1))

    def test_get_route_info(self):
        for route in self.expected_routes:
            self.assertEqual(self.config._get_route_info(route), self.config._quick_routes[route])

    def test_get_api_route(self):
        for route in self.expected_routes:
            r_info = self.config._get_route_info(route)
            for version in r_info["Versions"]:
                partial_route = self.config._quick_routes[route]["Route"]
                self.assertEqual("/rec/v{0}/{1}/".format(version, partial_route), self.config.get_api_route(route, version))
                if version == 1 and route == "User Recordings Ribbon":
                    self.assertEqual("/rec/v1/user-recordings/", self.config.get_api_route(route, version))

    def test_get_api_host(self):
        for env in self.expected_api_env:
            max_node = self.config._quick_api_env[env]["Total Nodes"]
            min_node = 0
            VIP_host = self.config._quick_api_env[env]["VIP Host"]
            node_host = self.config._quick_api_env[env]["Node Host"]
            self.assertEqual(self.config.get_api_host(env, 0), "http://" + VIP_host)
            while min_node < max_node:
                min_node += 1
                self.assertEqual(self.config.get_api_host(env, min_node), "http://" + node_host.format(min_node))

            self.assertEqual(self.config.get_api_host(env, max_node + 1), None)

    def test_get_env_hosts_api(self):
        for env in self.expected_api_env:
            expected_hosts = {"VIP": self.config.get_api_host(env, 0), "Node": [self.config.get_api_host(env, node) for node in range(1, self.config.get_total_api_nodes(env) + 1)]}
            self.assertEqual(expected_hosts, self.config.get_api_env_hosts(env))
            self.assertEqual(self.config.get_total_api_nodes(env), len(self.config.get_api_env_hosts(env)["Node"]))

    def test_get_api_version_fields(self):
        for route in self.expected_routes:
            api_route_spec = self.config.get_api_version_fields(route)
            versions_set = self.config.get_route_versions(route)
            self.assertEqual(versions_set, api_route_spec.keys())
            for values in api_route_spec.keys():
                self.assertEqual(api_route_spec[values].keys(), ["Required Fields", "Optional Fields"])

    def test_misc_routes(self):
        for route in self.Expected_misc_tests:
            self.assertTrue(self.config.is_route(route))

    def test_get_test_setup(self):
        user_recordings_setup = self.config.get_test_setup("Node User Recordings")
        self.assertItemsEqual(self.Expected_setup_params, set(user_recordings_setup.keys()), "The test setup did not contain all neccesary keys")
