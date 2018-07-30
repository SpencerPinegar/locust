import json
import logging
import os

from locust import HttpLocust, TaskSet
import locust.stats
from requests.exceptions import RequestException

from API_Load_Test.Config.config import Config
from API_Load_Test.environment_wrapper import EnvironmentWrapper
from API_Load_Test.request_pool import RequestPoolFactory



logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
SECONDS = 1000




# TODO: ADD POOLS FOR CREATE/DELETE OPERATIONS -- create/delete recordings, create/delete recording rules



class APITasks(TaskSet):

    expected_keys = ["API_CALL_WEIGHT", "VERSION", "NODE", "ENV", "N_MIN", "N_MAX", "STAT_INTERVAL"]


    #TODO: make sure that this is supported, if not make it supported by importing from master
    def setup(self):
        APITasks.setup_based_on_env_vars()


    def _user_recordings_ribbon(locust):
        json_data = APITasks.user_recordings_pool.get_json()
        APITasks.post_json_csm_copy(locust, json_data, APITasks.urr_url)



    def _user_franchise_ribbon(locust):
        json_data = APITasks.user_franchise_pool.get_json()
        locust.client.post(APITasks.ufr_url, json=json_data)



    def _user_recspace_information(locust):
        json_data = APITasks.user_recspace_info_pool.get_json()
        locust.client.post(APITasks.uri_url, json=json_data)




    def _update_user_settings(locust):
        json_data = APITasks.update_user_settings_pool.get_json()
        locust.client.post(APITasks.uus_url, json=json_data)



    def _protect_recordings(locust):
        json_data = APITasks.protect_recordings_pool.get_json()
        locust.client.post(APITasks.pr_url, json=json_data)




    def _mark_watched(locust):
        json_data = APITasks.marked_watched_pool.get_json()
        locust.client.post(APITasks.mw_url, json=json_data)




    def _update_user_rules(locust):
        json_data = APITasks.update_rules_pool.get_json()
        locust.client.post(APITasks.ur_url, json=json_data)



    def _list_user_rules(locust):
        json_data = APITasks.list_rules_pool.get_json()
        locust.client.post(APITasks.lr_url, json=json_data)


    def _nothing(self):
        assert 2 + 2 == 4
        pass



    #def _create_delete_rules(locust):
    #    json_data

    _task_method_realtion = {
        "User Recordings Ribbon": _user_recordings_ribbon,
        "User Franchise Ribbon": _user_franchise_ribbon,
        "User Recspace Information": _user_franchise_ribbon,
        "Update User Settings": _update_user_settings,
        "Protect Recordings": _protect_recordings,
        "Mark Watched": _mark_watched,
        "Update Rules": _update_user_rules,
        "List Rules": _list_user_rules,
        "Nothing": _nothing,
    }





    BENCHMARK = .25 * SECONDS
    SLOW = .5 * SECONDS
    VERY_SLOW = 1 * SECONDS
    USER_WAITING = 3 * SECONDS
    CMS_TIMEOUT = 6 * SECONDS #TODO: make this come from test config file


    @classmethod
    def setup_based_on_env_vars(cls):
        env_wrapper = EnvironmentWrapper(os.environ.copy())
        for key in APITasks.expected_keys:
            assert key in env_wrapper.keys()

        cls.env = env_wrapper.get("ENV")
        cls.version = env_wrapper.get("VERSION")
        node = env_wrapper.get("NODE")
        cls.node = "VIP" if node is 0 else node
        cls.api_call_weight = env_wrapper.get("API_CALL_WEIGHT")

        normal_min = env_wrapper.get("N_MIN")
        normal_max = env_wrapper.get("N_MAX")
        stat_interval = env_wrapper.get("STAT_INTERVAL")
        locust.stats.CSV_STATS_INTERVAL_SEC = stat_interval
        pool_factory = RequestPoolFactory(Config(), [cls.env])

        cls._set_tasks()
        for api_call in cls.api_call_weight.keys():
            if api_call == "User Recordings Ribbon":
                cls.user_recordings_pool, cls.urr_url = pool_factory.get_user_recordings_ribbon_pool_and_route(cls.version, cls.env,
                                                                                                       normal_min,
                                                                                                       normal_max)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "User Franchise Ribbon":
                cls.user_franchise_pool, cls.ufr_url = pool_factory.get_user_franchise_ribbon_pool_and_route(cls.version, cls.env,
                                                                                                             normal_min,
                                                                                                             normal_max)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "User Recspace Information":
                cls.user_recspace_info_pool, cls.uri_url = pool_factory.get_user_recspace_information_pool_and_route(cls.version,
                                                                                                             cls.env,
                                                                                                             normal_min,
                                                                                                             normal_max)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "Update User Settings":
                cls.update_user_settings_pool, cls.uus_url = pool_factory.get_update_user_settngs_pool_and_route(cls.version, cls.env,
                                                                                                         normal_min,
                                                                                                         normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            elif api_call == "Protect Recordings":
                cls.protect_recordings_pool, cls.pr_url = pool_factory.get_protect_recordings_pool_and_route(cls.version, cls.env,
                                                                                                     normal_min,
                                                                                                     normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            elif api_call == "Mark Watched":
                cls.marked_watched_pool, cls.mw_url = pool_factory.get_mark_watched_pool_and_route(cls.version, cls.env, normal_min,
                                                                                           normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            elif api_call == "Update Rules":
                cls.update_rules_pool, cls.ur_url = pool_factory.get_update_rules_pool_and_route(cls.version, cls.env, normal_min,
                                                                                         normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            elif api_call == "List Rules":
                cls.list_rules_pool, cls.lr_url = pool_factory.get_list_rules_pool_and_route(cls.version, cls.env, normal_min, normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            elif api_call == "Nothing":
                logger.debug("Set up {0} Info".format(api_call))
            else:
                logger.error("{0} is not a valid API call - valid api calls {1}".format(api_call, APITasks._task_method_realtion.keys()))


    @classmethod
    def _set_tasks(cls):
        tasks_to_be = []
        for api_call in cls.api_call_weight.keys():
            api_call = api_call.title()
            if api_call not in APITasks._task_method_realtion.keys():
                logger.error("{0} is not a valid api call".format(api_call))
            for add_task_count in range(cls.api_call_weight[api_call]):
                tasks_to_be.append(APITasks._task_method_realtion[api_call])
        cls.tasks = tasks_to_be
        logger.debug("tasks set to {0}".format(tasks_to_be))


    @staticmethod
    def post_json_csm_copy(locust, json_info, url):
        """
        This function assumes that all requests must be under the designated max response time, close after,
        and that the resposne code must be 200
        :param locust:
        :param json_info:
        :param url:
        :return:
        """

        header = {"Content-Type": "application/json", "Connection": "close"}
        call_name = "{env}-{node}--{route}".format(env=APITasks.env, node=APITasks.node, route=url)

        with locust.client.request("POST", url, name=call_name, catch_response=True, data=json.dumps(json_info), headers=header) as response:
            try:
                response.raise_for_status()
            except RequestException as e:
                response.failure(e)
            if response.locust_request_meta["response_time"] < APITasks.BENCHMARK:
                response.locust_request_meta["name"] = "0 PASS < {time}ms: {name}".format(
                    name=response.locust_request_meta["name"], time=APITasks.BENCHMARK)
                response.success()
            elif response.locust_request_meta["response_time"] < APITasks.SLOW:
                response.locust_request_meta["name"] = "1 SLOW {below}ms -- {above}ms: {name}".format(
                    name=response.locust_request_meta["name"], below=APITasks.BENCHMARK, above=APITasks.SLOW)
                response.success()
            elif response.locust_request_meta["response_time"] < APITasks.VERY_SLOW:
                response.locust_request_meta["name"] = "2 VERY SLOW {below}ms -- {above}ms: {name}".format(
                    name=response.locust_request_meta["name"], below=APITasks.SLOW, above=APITasks.VERY_SLOW)
                response.success()
            elif response.locust_request_meta["response_time"] < APITasks.USER_WAITING:
                response.locust_request_meta["name"] = "3 USER WAIT {below}ms -- {above}ms: {name}".format(
                    name=response.locust_request_meta["name"], below=APITasks.VERY_SLOW, above=APITasks.USER_WAITING)
                response.success()
            elif response.locust_request_meta["response_time"] < APITasks.CMS_TIMEOUT:
                response.locust_request_meta["name"] = "4 LONG USER WAIT {below}ms -- {above}ms: {name}".format(
                    name=response.locust_request_meta["name"], below=APITasks.USER_WAITING, above=APITasks.CMS_TIMEOUT)
                response.success()
            else:
                response.locust_request_meta["name"] = "5 TIMEOUT >{timeout}ms: {name}".format(
                    name=response.locust_request_meta["name"], timeout=APITasks.CMS_TIMEOUT)
                response.success()





class APIUser(HttpLocust):
    """
    Locust user class that does requests to the API_Load_Test web server running on localhost
    """

    min_wait = 1 * SECONDS
    max_wait = 1 * SECONDS
    task_set = APITasks








