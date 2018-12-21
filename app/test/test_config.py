from app.Data.config import Config
from app.Utils.locust_test import LocustTest
import os
from collections import namedtuple

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
    Expected_program_name = "LoadRunner"

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

    def test_program_name(self):
        self.assertEqual(TestLoadRunnerSettings.Expected_program_name, self.config.program_name)






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

    expected_envs = {
        "DEV1",
        "DEV2",
        "DEV3",
        "QA",
        "BETA",
        "BETA2",
    }
    env_is_env_result_table = {
        "DEV1": True,
        "DEV2": True,
        "DEV3": True,
        "QA": True,
        "BETA": True,
        "BETA2": True,
        "NOT": False
    }
    Test_Info = {
        "metadata": {
            "route":  r"/mds/v{version}/{suf}",
            "routes": { "Get Asset Json", "Get Asset Jpeg", "Load Asset", "Get Airing", "Load Airing"},
            "route_suff": {
                             "Get Asset Json": "asset/{sched_guid}.json",
                             "Get Asset Jpeg": "asset/{sched_guid}.jpg",
                             "Load Asset": "asset",
                             "Get Airing": "airing",
                             "Load Airing": "airing"
                           },
            "env_max_node":  {
                             "DEV1": 3,
                             "DEV2": 2,
                             "DEV3": 3,
                             "QA": 3,
                             "BETA": 3,
                             "BETA2": 3,
                             },
            "route_versions": {
                             "Get Asset Json": [1], "Get Asset Jpeg": [1], "Load Asset": [1],
                             "Get Airing": [1], "Load Airing": [1], "Not Route": [],
                              },
            "eligible_route":{
                             "Get Asset Json": True, "Get Asset Jpeg": True, "Load Asset": True,
                             "Get Airing": True, "Load Airing": True, "Not Route": False,
                             },
            "env_hosts": {
                                 "DEV1": ("d-cg17-dvrmeta.movetv.com", "d-gp2-dvrmeta-{0}.imovetv.com"),
                                 "DEV2": ("d-cg17-dvrmeta2-1.movetv.com", "d-gp2-dvrmeta2-{0}.imovetv.com"),
                                 "DEV3": ("d-cg17-dvrmeta3.movetv.com", "d-gp2-dvrmeta3-{0}.imovetv.com"),
                                 "QA": ("q-cg17-dvrmeta.movetv.com", "q-gp2-dvrmeta-{0}.imovetv.com"),
                                 "BETA": ("b-cg17-dvrmeta.movetv.com", "b-gp2-dvrmeta-{0}.imovetv.com"),
                                 "BETA2": ("b-cg17-dvrmeta2.movetv.com", "b-gp2-dvrmeta2-{0}.imovetv.com")
                        }
        },
        "recapi": {
            "route":  r"/rec/v{version}/{suf}/",
            "routes":  { "User Recordings Ribbon", "User Franchise Ribbon", "User Recspace Information",
                         "Update User Settings", "Create Recordings", "Protect Recordings", "Mark Watched",
                         "Delete Recordings", "Create Rules", "Update Rules", "Delete Rules", "List Rules"
                         },
            "route_suff": {
                            "User Recordings Ribbon": "user-recordings",
                            "User Franchise Ribbon": "user-franchise-recordings",
                            "User Recspace Information": "user-recspace",
                            "Update User Settings": "user-update",
                            "Create Recordings": "rec-create",
                            "Protect Recordings": "rec-save",
                            "Mark Watched": "rec-watched",
                            "Delete Recordings": "rec-delete",
                            "Create Rules": "rule-create",
                            "Update Rules": "rule-update",
                            "Delete Rules": "rule-delete",
                            "List Rules": "user-recrules"
                          },
            "env_max_node":{
                           "DEV1": 2,
                           "DEV2": 6,
                           "DEV3": 6,
                           "QA": 2,
                           "BETA": 6,
                            "BETA2": 2,
                            },
            "route_versions": {
                             "User Recordings Ribbon": [1, 2, 4, 5], "User Franchise Ribbon": [1, 4],
                             "User Recspace Information": [1], "Update User Settings": [1], "Create Recordings": [1, 4],
                             "Protect Recordings": [1],  "Mark Watched": [1], "Delete Recordings": [1],
                             "Create Rules": [1, 4], "Update Rules": [1], "Delete Rules": [1], "List Rules": [1, 4],
                             },
            "eligible_route": {
                             "User Recordings Ribbon": True, "User Franchise Ribbon": True,
                             "User Recspace Information": True, "Update User Settings": True, "Create Recordings": True,
                             "Protect Recordings": True, "Mark Watched": True, "Delete Recordings": True,
                             "Create Rules": True, "Update Rules": True, "Delete Rules": True, "List Rules": True,
                             "Not": False, "A": False, "Listing": False
                             },
            "env_hosts": {
                             "DEV1": ("d-cg17-dvrapi.movetv.com", "d-gp2-recapi-{0}.imovetv.com"),
                             "DEV2": ("d-cg17-dvrapi2-1.movetv.com", "d-gp2-dvrapi2-{0}.imovetv.com"),
                             "DEV3": ("d-cg17-dvrapi3-1.movetv.com", "d-gp2-dvrapi3-{0}.imovetv.com"),
                             "QA": ("q-cg17-dvrapi.movetv.com", "q-gp2-recapi-{0}.imovetv.com"),
                            "BETA": ("b-cg17-recapi.movetv.com", "b-gp2-recapi-{0}.b.movetv.com"),
                            "BETA2": ("b-cg17-dvrapi2.b.movetv.com", "b-gp2-dvrapi2-{0}.imovetv.com")
                         },



        }
    }

    def test_prefix(self):
        service_prefix_table = {
            "recapi": TestAPIManager.Test_Info["recapi"]["route"],
            "metadata": TestAPIManager.Test_Info["metadata"]["route"]
        }
        for service_name, expected_prefix in service_prefix_table.items():
            service = getattr(self.config, service_name)
            actual_prefix = service.prefix
            self.assertEqual(expected_prefix, actual_prefix, "Expected:{0}, Actual:{1}".format(expected_prefix,
                                                                                                actual_prefix))
    def test_envs(self):

        service_expected_evs_table = {
            "recapi": TestAPIManager.expected_envs,
            "metadata": TestAPIManager.expected_envs
        }
        for service_name, exp_envs in service_expected_evs_table.items():
            service = getattr(self.config, service_name)
            act_envs = service.envs
            self.assertSetEqual(set(exp_envs), set(act_envs), "Expected:{0}, Actual:{1}".format(exp_envs,
                                                                                    act_envs))
    def test_routes(self):
        service_exp_routes_table = {
            "recapi": TestAPIManager.Test_Info["recapi"]["routes"],
            "metadata": TestAPIManager.Test_Info["metadata"]["routes"]
        }
        for service_name, exp_routes in service_exp_routes_table.items():
            service = getattr(self.config, service_name)
            act_routes = set(service.routes)
            self.assertSetEqual(exp_routes, act_routes, "Expected:{0}, Actual:{1}".format(exp_routes, act_routes))

    def test_is_eligible_route(self):

        service_exp_result_table = {
            "recapi": TestAPIManager.Test_Info["recapi"]["eligible_route"],
            "metadata": TestAPIManager.Test_Info["metadata"]["eligible_route"]
        }
        for service_name, eligible_route_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for route_name, exp_eligible in eligible_route_table.items():
                actl_eligible = service.is_eligible_route(route_name)
                self.assertEqual(exp_eligible, actl_eligible, "{3} {0} Expected:{1}, {0} Actual:{2}".format(
                 service_name, exp_eligible, actl_eligible, route_name
                ))

    def test_get_version_fields(self):
        pass

    def test_is_node(self):

        service_exp_result_table = {
            "recapi": TestAPIManager.Test_Info["recapi"]["env_max_node"],
            "metadata":TestAPIManager.Test_Info["metadata"]["env_max_node"],
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
        service_exp_result_table = {
            "recapi": TestAPIManager.env_is_env_result_table,
            "metadata": TestAPIManager.env_is_env_result_table
        }
        for service_name, exp_result_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for environ, exp_is_env in exp_result_table.items():
                act_is_env = service.is_env(environ)
                self.assertEqual(exp_is_env, act_is_env, "{0} Expected:{1}, {0} Actual:{2}".format(
                    service_name, exp_is_env, act_is_env
                ))

    def test_get_route(self):
        service_exp_result_table = {
            "recapi": TestAPIManager.Test_Info["recapi"]["route"],
            "metadata": TestAPIManager.Test_Info["metadata"]["route"]
        }
        for service_name, route_base in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for route, exp_suff in TestAPIManager.Test_Info[service_name]["route_suff"].items():
                versions = TestAPIManager.Test_Info[service_name]["route_versions"][route]
                for version in versions:
                    exp = route_base.format(version=version, suf=exp_suff)
                    act = service.get_route(route, version)
                    self.assertEqual(exp, act, "{0} {1} Expected:{2}, Actual:{3}".format(
                        service_name, route, exp, act
                    ))

    def test_get_host(self):
        service_exp_result_table ={
            "recapi": TestAPIManager.Test_Info["recapi"]["env_hosts"],
            "metadata": TestAPIManager.Test_Info["metadata"]["env_hosts"]
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

    def test_get_total_nodes(self):
        service_exp_result_table = {
            "recapi": TestAPIManager.Test_Info["recapi"]["env_max_node"],
            "metadata": TestAPIManager.Test_Info["metadata"]["env_max_node"]
        }
        for service_name, exp_result_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for env, exp_max_node in exp_result_table.items():
                act_max_node = service.get_total_nodes(env)
                self.assertEqual(exp_max_node, act_max_node, "{0} {1} Expected Max: {2}, Actual Max: {3}".format(
                    service_name, env, exp_max_node, act_max_node
                ))

    def test_get_route_versions(self):
        service_exp_result_table = {
            "recapi": TestAPIManager.Test_Info["recapi"]["route_versions"],
            "metadata": TestAPIManager.Test_Info["metadata"]["route_versions"]
        }
        for service_name, route_version_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for route_name, exp_versions in route_version_table.items():
                act_verisons = service.get_route_versions(route_name)
                self.assertEqual(exp_versions, act_verisons, "{3} {0} Expected:{1}, {0} Actual:{2}".format(
                 service_name, exp_versions, act_verisons, route_name
                ))

    def test_is_version(self):
        service_exp_result_table = {
            "recapi": TestAPIManager.Test_Info["recapi"]["route_versions"],
            "metadata": TestAPIManager.Test_Info["metadata"]["route_versions"]
        }
        for service_name, route_version_table in service_exp_result_table.items():
            service = getattr(self.config, service_name)
            for route_name, exp_versions in route_version_table.items():
                act_verisons = service.get_route_versions(route_name)
                self.assertEqual(exp_versions, act_verisons, "{3} {0} Expected:{1}, {0} Actual:{2}".format(
                    service_name, exp_versions, act_verisons, route_name
                ))



