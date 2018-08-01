
"""
Most Recent Valid Testing: June 25, 2018
"""
import logging
import os
import yaml #PYYAML
import psycopg2 #psycopg2
from API_Load_Test.Config.sql_route_statements import SQL_ROUTES_STATEMENTS

HERE = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(HERE)




logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)


class Config(object):

    SETTINGS_PATH = os.path.join(DIR_PATH, "SETTINGS.yaml")

    def __init__(self, debug=False):

        self.debug = debug
        self._settings = self._build_settings()
        self._quick_routes = self._settings["RecAPI Settings"]["Routes"]
        self._quick_api_env = self._settings["RecAPI Settings"]["Environments"]




    @property
    def settings(self):
        return self._settings


    @property
    def api_envs(self):
        return self.settings["RecAPI Settings"]["Environments"].keys()


    @property
    def api_routes(self):
        return self.settings["RecAPI Settings"]["Routes"].keys()






    def get_api_routes(self, route_name):
        """
        Returns a list of version routes configured for the specific route:
            Ex: [
                "/rec/v1/user-franchise-recordings",
                "/rec/v4/user-franchise-recordings",
                ]6R^R
        :param route_name: The name of the route
        """
        api_routes = {}
        for version in self.get_route_versions(route_name):
            api_routes.setdefault(version, self.get_api_route(route_name, version))
        return api_routes


    def get_api_version_fields(self, route_name):
        """
        Returns a dictionary with the version info with required/optional fields
            Ex: { 1: {
        :param route_name:
        :return:
        """
        version_info = {}
        route_name = route_name.title()
        if self.is_route(route_name):
            for version in self.get_route_versions(route_name):
                 version_info.setdefault(version, self._get_route_info(route_name)["Version {0}".format(version)])
        return version_info


    def get_api_route_specs(self, route):
        route = route.title()
        sql = SQL_ROUTES_STATEMENTS[route]
        version_info = self.get_api_version_fields(route)
        min, max = self.get_api_route_normal_min_max(route)
        is_list = self._get_route_info(route)["List"]
        return sql, version_info, min, max, is_list


    def get_api_route_normal_min_max(self, route):
        route = route.title()
        info = self._get_route_info(route)
        min = info["Normal Min"]
        max = info["Normal Max"]
        return min, max



    def get_api_env_hosts(self, env):
        hosts= {}
        vip_host = self.get_api_host(env, 0)
        node_hosts = [self.get_api_host(env, node) for node in range(1, self.get_total_api_nodes(env) + 1)]
        hosts.setdefault("VIP", vip_host)
        hosts.setdefault("Node", node_hosts)
        return hosts


    def get_db_connection(self, Env):
        env = Env.upper()
        db_envs = self.settings["DataBase Settings"]["Environments"].keys()
        if env in db_envs:
            name, user, pw, host, port = self._get_db_info(env)
            conn = psycopg2.connect(database=name, user=user, password=pw, host=host, port=port)
            self._verbose_log("Successfully built connection from Environment {0}".format(Env))
            return conn
        else:
            Config._error_param_not_found("Env", Env, db_envs)




    def get_api_route(self, route_name, version):
        route_name = route_name.title()
        assert isinstance(version, int)
        if self.is_route(route_name):
            if self.is_version(route_name, version):
                partial_route = self._quick_routes[route_name]["Route"]
                complete_route = "/rec/v{0}/{1}/".format(version, partial_route)
                return complete_route



    def get_api_host(self, env, node = 0):
        env = env.upper()

        assert isinstance(node, int)
        if self.is_api_env(env):
            if self.is_node(env, node):
                host = "http://{0}".format(self._get_host(env, node))
                return host






    def get_total_api_nodes(self, env):
        return self._quick_api_env[env]["Total Nodes"]

    def get_route_versions(self, route):
        return self._quick_routes[route]["Versions"]

    def get_db_environments(self):
        return self.settings["DataBase Settings"]["Environments"].keys()


    def _get_db_info(self, Env):
        env_info = self.settings["DataBase Settings"]["Environments"][Env]
        cred_info = self.settings["DataBase Settings"]["Credentials"]
        name = cred_info["DataBase Name"]
        user = cred_info["DataBase Username"]
        pw = cred_info["DataBase Password"]
        host = env_info["Host"]
        port = env_info["Port"]
        return name, user, pw, host, port



    def _get_route_info(self, route_name):
        return self._quick_routes[route_name]

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


    def _get_host(self, env, node):
        if node == 0:
            host = self._quick_api_env[env]["VIP Host"]
        else:
            host = self._quick_api_env[env]["Node Host"].format(node)
        return host


    def is_version(self, route_name, version):
        if version in self.get_route_versions(route_name):
            self._verbose_log("Found Version {0} for Route {1}".format(version, route_name))
            return True
        else:
            Config._error_param_not_found("Version", version, "{0} Versions {1}".format(route_name, self.get_route_versions(route_name)))
            return False

    def is_route(self, route_name):
        if route_name in self.api_routes:
            self._verbose_log("Found Route Name {0}".format(route_name))
            return True
        else:
            Config._error_param_not_found("Route Name", route_name, self.api_routes)
            return False

    def is_node(self, env, node):
        if 0 <= node <= self.get_total_api_nodes(env):
            self._verbose_log("Found Node {0}".format(node))
            return True
        else:
            Config._error_param_not_found("Node", node, "0 - {0}".format(self.get_total_api_nodes(env)))
            return False

    def is_api_env(self, Env):
        if Env in self.api_envs:
            self._verbose_log("Found API Env {0}".format(Env))
            return True
        else:
            Config._error_param_not_found("Env", Env, self.api_envs)
            return False



    def _verbose_log(self, msg):
        if self.debug:
            logger.debug(msg)

    @classmethod
    def _error_param_not_found(cls, param_name, entered_param, known_param):
        logger.debug("{0} is not a known {1} --- Known {1}: {2}".format(entered_param, param_name, known_param))











