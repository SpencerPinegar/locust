from unittest import TestCase
from Load_Test.Config.config import Config
import os
from Load_Test.test.api_test import APITest

class TestConfig(APITest):

    def setUp(self):

        APITest.setUp(self)
        self.expected_database_base = {"Environments", "Credentials"}
        self.expected_db_env = {"DEV1", "DEV2", "DEV3", "QA", "BETA", "BETA2", "PROD"}
        self.expected_db_env_params = {"Host", "Port"}
        self.expected_credentials_set = {"DataBase Name", "DataBase Username", "DataBase Password"}


        self.expected_routes_params = {"Route", "Versions", "Normal Min", "Normal Max", "Version 1", "List"}
        self.expected_api_env_params = {"VIP Host", "Node Host", "Total Nodes"}
        self.expected_api_base = {"Environments", "Routes"}



    def test_file_exists(self):
       self.assertTrue(os.path.exists(Config.SETTINGS_PATH))


    def test_build_settings_database_initial(self):
        try:

            actual_database_base = set(self.config._settings["DataBase Settings"].keys())
            self.assertSetEqual(self.expected_database_base, actual_database_base)
        except Exception as e:
            self.fail(e)


    def test_build_settings_database_enviorments(self):
        try:

            actual_db_env = set(self.config._settings["DataBase Settings"]["Environments"])
            self.assertSetEqual(self.expected_db_env, actual_db_env)


            for env in actual_db_env:
                actual_db_env_params = set(self.config._settings["DataBase Settings"]["Environments"][env])
                self.assertSetEqual(self.expected_db_env_params, actual_db_env_params)
        except Exception as e:
            self.fail(e)

    def test_build_settings_database_credentials(self):
        try:

            actual_credentials_set = set(self.config._settings["DataBase Settings"]["Credentials"].keys())
            self.assertSetEqual(self.expected_credentials_set, actual_credentials_set)

        except KeyError as e:
            self.fail("Could Not find key {0} in settings".format(e))

        except Exception as e:
            self.fail(e)

    def test_recAPI_initial(self):
        try:

            actual_api_base = set(self.config._settings["RecAPI Settings"].keys())
            self.assertSetEqual(self.expected_api_base, actual_api_base)
        except Exception as e:
            self.fail(e)

    def test_recAPI_enviorments(self):
        try:

            acutal_api_env = set(self.config._settings["RecAPI Settings"]["Environments"])
            self.assertSetEqual(self.expected_api_env, acutal_api_env)


            for env in acutal_api_env:
                acutal_api_env_params = set(self.config._settings["RecAPI Settings"]["Environments"][env].keys())
                self.assertSetEqual(self.expected_api_env_params, acutal_api_env_params)
        except Exception as e:
            self.fail(e)

    def test_recAPI_routes(self):
        try:

            actual_routes = set(self.config._settings["RecAPI Settings"]["Routes"].keys())
            self.assertSetEqual(self.expected_routes, actual_routes)


            for route in actual_routes:
                actual_routes_params = set(self.config._settings["RecAPI Settings"]["Routes"][route].keys())
                for needed_param in self.expected_routes_params:
                    self.assertTrue(actual_routes_params.__contains__(needed_param))
        except Exception as e:
            self.fail(e)


    def test_is_api_env(self):
        for env in self.expected_api_env:
            self.assertTrue(self.config._is_api_env(env))
        self.assertFalse(self.config._is_api_env("NOTAPIENV"))


    def test_is_node(self):
        for env in self.expected_api_env:
            max_node = self.config._quick_api_env[env]["Total Nodes"]
            min_node = 0
            self.assertTrue(self.config._is_node(env, max_node))
            self.assertTrue(self.config._is_node(env, min_node))
            self.assertTrue(self.config._is_node(env, max_node - 1))
            self.assertFalse(self.config._is_node(env, max_node + 1))
            self.assertFalse(self.config._is_node(env, min_node - 1))


    def test_is_route(self):
        for route in self.expected_routes:
            self.assertTrue(self.config._is_route(route))
        self.assertFalse(self.config._is_route("ISNOTROUTE"))

    def test_is_version(self):
        for route in self.expected_routes:
            info = self.config._get_route_info(route)
            for version in info["Versions"]:
                self.assertTrue(self.config._is_version(route, version))
                self.assertFalse(self.config._is_version(route, 0))

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


    def test_get_db_info(self):
        for env in self.expected_db_env:
            env_info = self.config._settings["DataBase Settings"]["Environments"][env]
            expected_credentials = ("dvrcloud", "dvrcloud", "dvrcloud_pw", env_info["Host"], env_info["Port"])
            self.assertEqual(self.config._get_db_info(env), expected_credentials)

    def test_get_db_connection(self):
        for env in self.expected_db_env:
            conn = self.config.get_db_connection(env)
            self.assertFalse(conn == None)

    def test_get_env_hosts_api(self):
        for env in self.expected_api_env:
            expected_hosts = {"VIP": self.config.get_api_host(env, 0), "Node": [self.config.get_api_host(env, node) for node in range(1, self.config.get_total_api_nodes(env) + 1)]}
            self.assertEqual(expected_hosts, self.config.get_api_env_hosts(env))
            self.assertEqual(self.config.get_total_api_nodes(env), len(self.config.get_api_env_hosts(env)["Node"]))

    def test_get_api_routes(self):
        for route in self.expected_routes:
            self.assertEqual(len(self.config._get_route_info(route)["Versions"]), len(self.config.get_route_versions(route)))
            for version, route in self.config.get_api_routes(route).items():
                self.assertTrue(route.__contains__(str(version)))

    def test_get_api_version_fields(self):
        for route in self.expected_routes:
            api_route_spec = self.config.get_api_version_fields(route)
            versions_set = self.config.get_route_versions(route)
            self.assertEqual(versions_set, api_route_spec.keys())
            for values in api_route_spec.keys():
                self.assertEqual(api_route_spec[values].keys(), ["Required Fields", "Optional Fields"])






