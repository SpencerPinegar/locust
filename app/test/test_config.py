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


class TestAPIManager(LocustTest):


    def test_prefix(self):
        service_prefix_table = {
            "recapi": r"/rec/v{version}/{suf}/",
            "metadata": r"/mds/v{version}/{suf}/"
        }
        for service_name, expected_prefix in service_prefix_table.items():
            service = getattr(self.config, service_name)
            actual_prefix = service.prefix
            self.assertEqual(expected_prefix, actual_prefix, "Expected:{0}, Actual:{1}".format(expected_prefix,
                                                                                                actual_prefix))
    def test_envs(self):
        expected_envs = {
            "DEV1",
            "DEV2",
            "DEV3",
            "QA",
            "BETA",
            "BETA2",
        }
        service_expected_evs_table = {
            "recapi": expected_envs,
            "metadata": expected_envs
        }
        for service_name, exp_envs in service_expected_evs_table.items():
            service = getattr(self.config, service_name)
            act_envs = service.envs
            self.assertSetEqual(set(exp_envs), set(act_envs), "Expected:{0}, Actual:{1}".format(exp_envs,
                                                                                    act_envs))
    def test_routes(self):
        service_exp_routes_table = {
            "recapi": {
                             "User Recordings Ribbon", "User Franchise Ribbon", "User Recspace Information",
                             "Update User Settings", "Create Recordings", "Protect Recordings", "Mark Watched",
                             "Delete Recordings", "Create Rules", "Update Rules", "Delete Rules", "List Rules"
                         },
            "metadata": {
                            "Get Asset Json", "Get Asset Jpeg", "Load Asset", "Get Airing", "Load Airing"
                         },
        }
        for service_name, exp_routes in service_exp_routes_table.items():
            service = getattr(self.config, service_name)
            act_routes = set(service.routes)
            self.assertSetEqual(exp_routes, act_routes, "Expected:{0}, Actual:{1}".format(exp_routes, act_routes))

    def test_is_eligible_route(self):
        recapi_eligible_route_table = {
            "User Recordings Ribbon": True,  "User Franchise Ribbon": True,  "User Recspace Information": True,
            "Update User Settings":   True,  "Create Recordings":     True,  "Protect Recordings":        True,
            "Mark Watched":           True,  "Delete Recordings":     True,  "Create Rules":              True,
            "Update Rules":           True,  "Delete Rules":          True,  "List Rules":                True,
            "Not":                    False, "A":                     False, "Listing":                   False
        }
        metadata_eligible_route_table = {
            "Get Asset Json":         True, "Get Asset Jpeg":         True,  "Load Asset":                True,
            "Get Airing":             True, "Load Airing":            True,  "Not Route":                 False,
        }
        service_exp_result_table = {
            "recapi": recapi_eligible_route_table,
            "metadata": metadata_eligible_route_table
        }
        for service_name, eligible_route_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for route_name, exp_eligible in eligible_route_table.items():
                actl_eligible = service.is_eligible_rotue(route_name)
                self.assertEqual(exp_eligible, actl_eligible, "{0} Expected:{1}, {0} Actual:{2}".format(
                 service_name, exp_eligible, actl_eligible
                ))

    def test_get_version_fields(self):
        pass

    def test_get_route_version(self):
        recapi_route_version_table = {
            "User Recordings Ribbon": [1,2,4,5], "User Franchise Ribbon": [1,4], "User Recspace Information": [1],
            "Update User Settings":   [1],       "Create Recordings":     [1,4], "Protect Recordings":        [1],
            "Mark Watched":           [1],       "Delete Recordings":     [1],    "Create Rules":             [1,4],
            "Update Rules":           [1],       "Delete Rules":          [1],    "List Rules":               [1,4],
        }
        metadata_route_version_table = {
            "Get Asset Json":         [1],       "Get Asset Jpeg":        [1],    "Load Asset":               [1],
            "Get Airing":             [1],       "Load Airing":           [1],    "Not Route":                [1],
        }
        service_exp_result_table = {
            "recapi": recapi_route_version_table,
            "metadata": metadata_route_version_table
        }
        for service_name, route_version_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for route_name, exp_versions in route_version_table.items():
                act_verisons = service.get_route_versions(route_name)
                self.assertEqual(exp_versions, act_verisons, "{0} Expected:{1}, {0} Actual:{2}".format(
                 service_name, exp_versions, act_verisons
                ))

    def test_is_node(self):
        recapi_env_and_max_node_test_table = {
            "DEV1":  2,
            "DEV2":  6,
            "DEV3":  6,
            "QA":    2,
            "BETA":  6,
            "BETA2": 2,
        }

        metadata_env_and_max_node_test_table = {
            "DEV1":  3,
            "DEV2":  2,
            "DEV3":  3,
            "QA":    3,
            "BETA":  3,
            "BETA2": 3,
        }
        service_exp_result_table = {
            "recapi": recapi_env_and_max_node_test_table,
            "metadata": metadata_env_and_max_node_test_table,
        }
        for service_name, exp_result_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for environ, max_node in exp_result_table.items():
                for i in range(1, max_node + 1):
                    self.assertTrue(service.is_node(environ, i),
                                    "{0} Expected {1} to be an eligible node".format(service_name, i)
                                    )
                for i in range(max_node + 1, max_node + 3):
                    self.assertFalse(service.is_node(environ, i),
                                    "{0} Expected {1} to be an ineligible node".format(service_name, i)
                                     )

    def test_is_env(self):
        env_is_env_result_table = {
            "DEV1":  True,
            "DEV2":  True,
            "DEV3":  True,
            "QA":    True,
            "BETA":  True,
            "BETA2": True,
            "NOT":   False
        }
        service_exp_result_table = {
            "recapi": env_is_env_result_table,
            "metadata": env_is_env_result_table
        }
        for service_name, exp_result_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for environ, exp_is_env in exp_result_table.items():
                act_is_env = service.is_env(environ)
                self.assertEqual(exp_is_env, act_is_env, "{0} Expected:{1}, {0} Actual:{2}".format(
                    service_name, exp_is_env, act_is_env
                ))

    def test_get_route(self):
        pass


    def test_get_host(self):
        metadata_envNnode_host_result_result_table = {
            "DEV1":  ("d-cg17-dvrmeta.movetv.com",    "d-gp2-dvrmeta-{0}.imovetv.com"),
            "DEV2":  ("d-cg17-dvrmeta2-1.movetv.com", "d-gp2-dvrmeta2-{0}.imovetv.com"),
            "DEV3":  ("d-cg17-dvrmeta3.movetv.com",   "d-gp2-dvrmeta3-{0}.imovetv.com"),
            "QA":    ("q-cg17-dvrmeta.movetv.com",    "q-gp2-dvrmeta-{0}.imovetv.com"),
            "BETA":  ("b-cg17-dvrmeta.movetv.com",    "b-gp2-dvrmeta-{0}.imovetv.com"),
            "BETA2": ("b-cg17-dvrmeta2.movetv.com",   "b-gp2-dvrmeta2-{0}.imovetv.com")
        }
        recapi_envNnode_host_result_result_table = {
            "DEV1":  ("d-cg17-dvrapi.movetv.com",      "d-gp2-recapi-{0}.imovetv.com"),
            "DEV2":  ("d-cg17-dvrapi2-1.movetv.com",   "d-gp2-dvrapi2-{0}.imovetv.com"),
            "DEV3":  ("d-cg17-dvrapi3-1.movetv.com",   "d-gp2-dvrapi3-{0}.imovetv.com"),
            "QA":    ("q-cg17-dvrapi.movetv.com",      "q-gp2-recapi-{0}.imovetv.com"),
            "BETA":  ("b-cg17-recapi.movetv.com",      "b-gp2-recapi-{0}.b.movetv.com"),
            "BETA2": ("b-cg17-dvrapi2.b.movetv.com",   "b-gp2-dvrapi2-{0}.imovetv.com")
        }
        service_exp_result_table ={
            "recapi": recapi_envNnode_host_result_result_table,
            "metadata": metadata_envNnode_host_result_result_table
        }
        for service_name, exp_result_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for env, hosts in exp_result_table.items():
                for node in range(service.get_total_nodes(env) + 1):
                    if node == 0:
                        exp_host = "http://" + hosts[0]
                        act_host = service.get_host(env, node)
                        self.assertEqual(exp_host, act_host,
                                         "{0} Expected VIP:{1}, {0} Actual VIP:{2}".format(
                                             service_name, exp_host, act_host
                                         ))
                    else:
                        exp_host = "http://" + hosts[1].format(node)
                        act_host = service.get_host(env, node)
                        self.assertEqual(exp_host, act_host, "{0} Expected Node:{1}, {0} Actual Node:{2}".format(
                            service_name, exp_host, act_host
                        ))




class TestMetaDataCongig(LocustTest):
    Expected_metadata_env_params = {"VIP Host", "Node Host", "Total Nodes"}


    def setUp(self):
        LocustTest.setUp(self)

    def test_metadata_prefix(self):
        expected_prefix = "/mds/v{version}/{suf}/"
        acutal_prefix = self.config.metadata.prefix
        self.assertEqual(acutal_prefix, expected_prefix, "Expected: {0}, Actual: {1}".format(
            expected_prefix, acutal_prefix
        ))

    def test_metadata_routes(self):
        expected_routes = {
            "Get Asset Json",
            "Get Asset Jpeg",
            "Load Asset",
            "Get Airing",
            "Load Airing",
        }
        actual_routes = set(self.config.metadata.routes)
        self.assertSetEqual(expected_routes, actual_routes, "Expected: {0}, Acutal: {1}".format(
            expected_routes, actual_routes
        ))

    def test_metadata_envs(self):
        self.assertSetEqual(self.expected_api_env, set(self.config.metadata.envs), "Meta Data Envs not working correctly")

    def test_is_meta_data_node(self):
        env_and_max_node_test_table = {
            "DEV1":  3,
            "DEV2":  2,
            "DEV3":  3,
            "QA":    3,
            "BETA":  3,
            "BETA2": 3,
        }
        for environ, max_node in env_and_max_node_test_table.items():

            for i in range(1, max_node+1):
                self.assertTrue(self.config.metadata.is_node(environ, i), "Expected {node} to be node for {env} - failing".format(
                    node=i, env=environ
                ))
            for i in range(max_node+1, max_node+3):
                self.assertFalse(self.config.metadata.is_node(environ, i), "Expected {node} to not be node for {env} - failing".format(
                    node=i, env=environ
                ))

    def test_is_metadata_env(self):
        potential_is_env_and_result_table = {
            "DEV1":  True,
            "DEV2":  True,
            "DEV3":  True,
            "QA":    True,
            "BETA":  True,
            "BETA2": True,
            "NOENV": False,
        }
        for pot_env, expected_result in potential_is_env_and_result_table.items():
            self.assertEqual(self.config.metadata.is_env(pot_env), expected_result, "Expected {env} to {exist} be Env".format(
                env=pot_env, exist="" if expected_result else "not"
            ))

    def test_get_total_metadata_nodes(self):
        env_and_max_node_test_table = {
            "DEV1":  3,
            "DEV2":  2,
            "DEV3":  3,
            "QA":    3,
            "BETA":  3,
            "BETA2": 3,
        }
        for env, max_node in env_and_max_node_test_table.items():
            self.assertEqual(self.config.metadata.get_total_nodes(env), max_node, "Expected {env} Max Node: {max},"
                                                                                  "Recieved {env} Max Node: {rec}".format(
                env=env, max=max_node, rec=self.config.metadata.get_total_nodes(env)
            ))

    def test_get_meta_data_host(self):
        envNnode_host_result_result_table = {
            "DEV1":  ("d-cg17-dvrmeta.movetv.com", "d-gp2-dvrmeta-{0}.imovetv.com"),
            "DEV2":  ("d-cg17-dvrmeta2-1.movetv.com", "d-gp2-dvrmeta2-{0}.imovetv.com"),
            "DEV3":  ("d-cg17-dvrmeta3.movetv.com", "d-gp2-dvrmeta3-{0}.imovetv.com"),
            "QA":    ("q-cg17-dvrmeta.movetv.com", "q-gp2-dvrmeta-{0}.imovetv.com"),
            "BETA":  ("b-cg17-dvrmeta.movetv.com", "b-gp2-dvrmeta-{0}.imovetv.com"),
            "BETA2": ("b-cg17-dvrmeta2.movetv.com", "b-gp2-dvrmeta2-{0}.imovetv.com")
        }
        for env, hosts in envNnode_host_result_result_table.items():
            for node in range(self.config.metadata.get_total_nodes(env)):
                if node == 0:
                    self.assertEqual(self.config.metadata.get_host(env, node), "http://" + hosts[0], "Wrong {env} VIP: {host}".format(
                        env=env, host=hosts[0]
                    ))
                else:
                    self.assertEqual(self.config.metadata.get_host(env, node), "http://" + hosts[1].format(node), "Wrong {env} Node: {host}".format(
                        env=env, host=hosts[1].format(node)
                    ))




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

    def test_recapi_prefix(self):
        expected_prefix = "/rec/v{version}/{suf}/"
        actual_prefix = self.config.recapi.prefix
        self.assertEqual(expected_prefix, actual_prefix, "Expected: {0}, Actual: {1}".format(expected_prefix,
                                                                                                         actual_prefix))

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
            self.assertTrue(self.config.recapi.is_env(env))
        self.assertFalse(self.config.recapi.is_env("NOTAPIENV"))

    def test_is_node(self):
        for env in self.expected_api_env:
            max_node = self.config._quick_api_env[env]["Total Nodes"]
            min_node = 0
            self.assertTrue(self.config.recapi.is_node(env, max_node))
            self.assertTrue(self.config.recapi.is_node(env, min_node))
            self.assertTrue(self.config.recapi.is_node(env, max_node - 1))
            self.assertFalse(self.config.recapi.is_node(env, max_node + 1))
            self.assertFalse(self.config.recapi.is_node(env, min_node - 1))

    def test_is_route(self):
        for route in self.expected_routes:
            self.assertTrue(self.config.is_eligible_route(route))
        self.assertFalse(self.config.is_eligible_route("ISNOTROUTE"))

    def test_is_version(self):
        for route in self.expected_routes:
            info = self.config.recapi._get_route_info(route)
            for version in info["Versions"]:
                self.assertTrue(self.config.recapi.is_version(route, version))
                self.assertFalse(self.config.recapi.is_version(route, 0))

    def test_get_host(self):
        for env in self.expected_api_env:
            self.assertEqual(self.config.recapi._get_host(env, 0), self.config._quick_api_env[env]["VIP Host"])
            self.assertEqual(self.config.recapi._get_host(env, 1), self.config._quick_api_env[env]["Node Host"].format(1))

    def test_get_route_info(self):
        for route in self.expected_routes:
            self.assertEqual(self.config.recapi._get_route_info(route), self.config._quick_routes[route])

    def test_get_api_route(self):
        for route in self.expected_routes:
            r_info = self.config.recapi._get_route_info(route)
            for version in r_info["Versions"]:
                partial_route = self.config._quick_routes[route]["Route"]
                self.assertEqual("/rec/v{0}/{1}/".format(version, partial_route), self.config.api.get_route(route, version))
                if version == 1 and route == "User Recordings Ribbon":
                    self.assertEqual("/rec/v1/user-recordings/", self.config.api.get_route(route, version))

    def test_get_api_host(self):
        for env in self.expected_api_env:
            max_node = self.config._quick_api_env[env]["Total Nodes"]
            min_node = 0
            VIP_host = self.config._quick_api_env[env]["VIP Host"]
            node_host = self.config._quick_api_env[env]["Node Host"]
            self.assertEqual(self.config.recapi.get_host(env, 0), "http://" + VIP_host)
            while min_node < max_node:
                min_node += 1
                self.assertEqual(self.config.recapi.get_host(env, min_node), "http://" + node_host.format(min_node))

            self.assertEqual(self.config.recapi.get_host(env, max_node + 1), None)

    def test_get_env_hosts_api(self):
        for env in self.expected_api_env:
            expected_hosts = {"VIP": self.config.recapi.get_host(env, 0), "Node": [self.config.recapi.get_host(env, node) for node in range(1, self.config.recapi.get_total_nodes(env) + 1)]}
            self.assertEqual(expected_hosts, self.config.recapi.get_env_hosts(env))
            self.assertEqual(self.config.recapi.get_total_nodes(env), len(self.config.recapi.get_env_hosts(env)["Node"]))

    def test_get_api_version_fields(self):
        for route in self.expected_routes:
            api_route_spec = self.config.recapi.get_version_fields(route)
            versions_set = self.config.recapi.get_route_versions(route)
            self.assertEqual(versions_set, api_route_spec.keys())
            for values in api_route_spec.keys():
                self.assertEqual(api_route_spec[values].keys(), ["Required Fields", "Optional Fields"])

    def test_misc_routes(self):
        for route in self.Expected_misc_tests:
            self.assertTrue(self.config.is_eligible_route(route))

    def test_get_test_setup(self):
        user_recordings_setup = self.config.get_test_setup("Node User Recordings")
        self.assertItemsEqual(self.Expected_setup_params, set(user_recordings_setup.keys()), "The test setup did not contain all neccesary keys")
