
"""
Most Recent Valid Testing: June 25, 2018
"""
import logging
import socket
import os
import yaml #PYYAML
import psycopg2 #psycopg2
from app.Data.sql_route_statements import SQL_ROUTES_STATEMENTS

HERE = os.path.abspath(__file__)
MAIN_DIR_PATH = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))




logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)


class Config(object):
    RecAPI_Name = "RecAPI"
    MetaData_Name = "MetaData"
    SETTINGS_PATH = os.path.join(MAIN_DIR_PATH, "SETTINGS.yaml")


    def __init__(self, debug=False):

        self.debug = debug
        self._settings = self._build_settings()
        self.recapi = APIManager(self._settings, Config.RecAPI_Name)
        self.metadata = APIManager(self._settings, Config.MetaData_Name)

##################################################################################################
##################################  General Settings ##############################################
##################################################################################################
    @property
    def test_routes(self):
        return self._settings["RecAPI"]["Extra Routes"]

    @property
    def settings(self):
        return self._settings

    def get_function_querry(self, function_route):
        return SQL_ROUTES_STATEMENTS[function_route]

    def is_eligible_route(self, route_name):
        if route_name in self.recapi.routes + self.test_routes + self.metadata.routes:
            self._verbose_log("Found Route Name {0}".format(route_name))
            return True
        else:
            Config._error_param_not_found("Route Name", route_name, self.recapi.routes)
            return False

    def _verbose_log(self, msg):
        if self.debug:
            logger.debug(msg)


    def _build_settings(self):
        """
        Finds the settings file and initilizes it from yaml to json
        :return:
        """
        self._verbose_log("Looking For Setting.yaml")
        try:
            with open(Config.SETTINGS_PATH, 'r') as settings:
                doc = yaml.load(settings)
                self._verbose_log("Found Settings.yaml")
                return doc
        except IOError as e:
            logger.critical("Could not find Setting.yaml file -- check Config File")
            logger.error(e)

    @classmethod
    def _error_param_not_found(cls, param_name, entered_param, known_param):
        logger.debug("{0} is not a known {1} --- Known {1}: {2}".format(entered_param, param_name, known_param))

##################################################################################################
##################################  Playback Settings ##############################################
##################################################################################################

    @property
    def playback_routes(self):
        return self.settings["Playback Settings"]["Playback Routes"]

    @property
    def playback_players(self):
        return self.settings["Playback Settings"]["Playback Players"]

##################################################################################################
##################################  Procedure Settings ##############################################
##################################################################################################

    def get_test_setup(self, name):
        return self.settings["Setups"][name]


    def get_test_procedure(self, name):
        return self.settings["Procedures"][name]

##################################################################################################
##################################  DataBase Settings ##############################################
##################################################################################################
    @property
    def db_envs(self):
        return self.settings["DataBase Settings"]["Environments"].keys()


    def get_db_connection(self, Env):
        env = Env.upper()
        if env in self.db_envs:
            name, user, pw, host, port = self._get_db_info(env)
            conn = psycopg2.connect(database=name, user=user, password=pw, host=host, port=port)
            self._verbose_log("Successfully built connection from Environment {0}".format(Env))
            return conn
        else:
            Config._error_param_not_found("Env", Env, self.db_envs)


    def _get_db_info(self, Env):
        env_info = self.settings["DataBase Settings"]["Environments"][Env]
        cred_info = self.settings["DataBase Settings"]["Credentials"]
        name = cred_info["DataBase Name"]
        user = cred_info["DataBase Username"]
        pw = cred_info["DataBase Password"]
        host = env_info["Host"]
        port = env_info["Port"]
        return name, user, pw, host, port


########################################################################################################################
##########################   DISTRIBUTED LOCUST TEST PROPERTIES                 ########################################
########################################################################################################################

    @property
    def rpc_port(self):
        return self.settings["LoadRunner Settings"]["RPC Settings"]["port"]

    @property
    def rpc_endpoint(self):
        return self.settings["LoadRunner Settings"]["RPC Settings"]["endpoint"]

    @property
    def locust_ui_port(self):
        return self.settings["LoadRunner Settings"]["Locust UI Settings"]["port"]

    @property
    def locust_ui_max_wait(self):
        return self.settings["LoadRunner Settings"]["Locust UI Settings"]["max wait"]

    @property
    def locust_port(self):
        return self.settings["LoadRunner Settings"]["Locust Runner Settings"]["port"]

    @property
    def response_time_cutoff_ms(self):
        return self.settings["LoadRunner Settings"]["Locust Runner Settings"]["SLA Response Time Cutoff ms"]

    @property
    def to_failure_max_consecutive_failed_frames(self):
        return self.settings["LoadRunner Settings"]["Locust Runner Settings"][
            "To Failure Max Consecutive Frames Failed"]

    @property
    def to_failure_procedure_prefix(self):
        return self.settings["LoadRunner Settings"]["Locust Runner Settings"]["To Failure Test Prefix"]

    @property
    def stat_reporting_interval(self):
        return self.settings["LoadRunner Settings"]["Locust Runner Settings"]["stat reporting interval"]

    @property
    def preferred_master(self):
        return self.settings["LoadRunner Settings"]["Servers"]["Potential Servers"][0]

    @property
    def potential_servers(self):
        return self.settings["LoadRunner Settings"]["Servers"]["Potential Servers"]

    @property
    def is_master(self):
        master_ip = str(socket.gethostbyname(self.preferred_master))
        my_ip = str(socket.gethostbyname(socket.getfqdn()))
        if master_ip == "127.0.1.1" or master_ip == my_ip:
            return True
        return False


class APIManager(object):

    Env_Key = "Environments"
    VIP_Key = "VIP Host"
    Node_Key = "Node Host"
    Total_Nodes_Key = "Total Nodes"

    API_Prefix_Key = "API Prefix"
    Routes_Key = "Routes"

    Route_Key = "Route"
    Versions_Key = "Versions"
    Normal_Min_Key = "Normal Min"
    Normal_Max_Key = "Normal Max"
    List_Key = "List"
    Version_Key = "Version {0}"
    RequiredF_Key = "Required Fields"
    OptionalF_Key = "Optional Fields"
    Extra_Host_Routes_Key = "Extra Routes"

    LayOut = {
        "USER DEFINED API SETTING NAME": {
            Env_Key: {
                "USER DEFINED ENV1": {
                    VIP_Key: "VIP HOST NAME",
                    Node_Key: "NODE HOST W/ NODE TO REPLACE",
                },
                "USER DEFINED ENV2": {
                    VIP_Key: "VIP HOST NAME",
                    Node_Key: "NODE HOST /W NODE TO REPALCE",
                }

            },
            API_Prefix_Key: "USER DEFINED API PREFIX",
            Routes_Key: {
                "USER DEFINED API ROUTE NAME": {
                    Route_Key: "API Route",
                    Versions_Key: "[1, 2]",
                    Normal_Min_Key: "Int Normal Key",
                    Normal_Max_Key: "Int Normal Key",
                    List_Key: "Is Outside Json List boolean",
                    Version_Key: {
                        RequiredF_Key: "User defined list of required fields",
                        OptionalF_Key: "User defined list of optional fields",
                    }
                },
            },
            Extra_Host_Routes_Key: [
                "extra route name to map1",
                "extra route name to map2",
                "extra route name to map3"
                 ]

        }
    }



    def __init__(self, settings, primary_name):
        self._relevant_api_info = settings[primary_name]
        self.extra_routes = self.settings[APIManager.Extra_Host_Routes_Key]
        self._quick_routes = self.settings[APIManager.Routes_Key]
        self._quick_env = self.settings[APIManager.Env_Key]
        self._versions = self.__build_version_list()


    @property
    def settings(self):
        return self._relevant_api_info


    @property
    def prefix(self):
        return self.settings[APIManager.API_Prefix_Key]

    @property
    def envs(self):
        return self.settings[APIManager.Env_Key].keys()

    @property
    def routes(self):
        return self.settings[APIManager.Routes_Key].keys()


    def is_eligible_route(self, route_name):
        if route_name in self.extra_routes + self.routes:
            return True
        return False


    def get_version_fields(self, route_name):
        """
        Returns a dictionary with the version info with required/optional fields
            Ex: { 1: {
        :param route_name:
        :return:
        """
        version_info = {}
        route_name = route_name.title()
        if self.is_eligible_route(route_name):
            for version in self.get_route_versions(route_name):
                 version_info.setdefault(version, self._get_route_info(route_name)[APIManager.Version_Key.format(version)])
        return version_info

    def is_node(self, env, node):
        if 0 <= node <= self.get_total_nodes(env):
            return True
        else:
            Config._error_param_not_found("Node", node, "0 - {0}".format(self.get_total_nodes(env)))
            return False

    def is_env(self, Env):
        if Env in self.envs:
            return True
        else:
            Config._error_param_not_found("Env", Env, self.envs)
            return False

    def get_route(self, route_name, version):
        route_name = route_name.title()
        assert isinstance(version, int)
        if self.is_eligible_route(route_name):
            if self.is_version(route_name, version):
                partial_route = self._quick_routes[route_name][APIManager.Route_Key]
                prefix = self.prefix
                complete_route = prefix.format(version=version, suf=partial_route)
                return complete_route

    def get_host(self, env, node = 0):
        env = env.upper()

        assert isinstance(node, int)
        if self.is_env(env):
            if self.is_node(env, node):
                host = "http://{0}".format(self._get_host(env, node))
                return host

    def get_total_nodes(self, env):
        return self._quick_env[env][APIManager.Total_Nodes_Key]

    def get_route_versions(self, route):
        try:
            return self._quick_routes[route][APIManager.Versions_Key]
        except KeyError:
            if route in self.extra_routes:
                return self._versions
            else:
                return []

    def is_version(self, route_name, version):
        if version in self.get_route_versions(route_name):
            return True
        else:
            Config._error_param_not_found("Version", version,
                                          "{0} Versions {1}".format(route_name, self.get_route_versions(route_name)))
            return False

    def get_route_specs(self, route):
        route = route.title()
        sql = SQL_ROUTES_STATEMENTS[route]
        version_info = self.get_version_fields(route)
        min, max = self.get_route_normal_min_max(route)
        is_list = self._get_route_info(route)[APIManager.List_Key]
        return sql, version_info, min, max, is_list


    def get_route_normal_min_max(self, route):
        route = route.title()
        info = self._get_route_info(route)
        min = info[APIManager.Normal_Min_Key]
        max = info[APIManager.Normal_Max_Key]
        return min, max



    def get_env_hosts(self, env):
        hosts= {}
        vip_host = self.get_host(env, 0)
        node_hosts = [self.get_host(env, node) for node in range(1, self.get_total_nodes(env) + 1)]
        hosts.setdefault("VIP", vip_host)
        hosts.setdefault("Node", node_hosts)
        return hosts


    def _get_route_info(self, route_name):
        return self._quick_routes[route_name]

    def _get_host(self, env, node):
        if node == 0:
            host = self._quick_env[env][APIManager.VIP_Key]
        else:
            host = self._quick_env[env][APIManager.Node_Key].format(node)
        return host


    def __build_version_list(self):
        versions = []
        for route in self.routes:
            versions = versions + self.get_route_versions(route)
        versions = set(versions)
        return versions
































