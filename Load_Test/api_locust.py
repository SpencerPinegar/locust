import json
import logging
import os

from locust import HttpLocust, TaskSet, task
import locust.stats
from requests.exceptions import RequestException

from Load_Test import Config, EnvironmentWrapper, RequestPoolFactory
import random
import hashlib


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


    def _redundant_ts_segment(locust):
        ts_url, ts_content_hash = random.choice(APITasks.ts_segment_urls)
        ts_prefix = ts_url.split("//")[1][0].lower()
        call_name = "{env} - ts request validation".format(env=ts_prefix, url=ts_url)
        with locust.client.get(ts_url,name=call_name, catch_response=True) as response:
            try:
                response.raise_for_status()
            except RequestException as e:
                response.failure(e)
            else:
                content = response.content
                created_content_hash = hashlib.md5(str(content)).hexdigest()
                if created_content_hash != ts_content_hash:
                    response.failure("Invalid TS Segment - Expected {ex}, Created {created}".format(ex=ts_content_hash, created=created_content_hash))
                else:
                    response.success()

    def _basic_network(locust):
        call_name = APITasks.__get_labeled_name("Basic Network Test")
        locust.client.post(APITasks.basic_network_url, name=call_name)


    def _network_byte_size(locust):
        payload = {"byte_size": "3"} #TODO Make this configurable - ideally by allowing params to be passed in with api_call_weight
        call_name = APITasks.__get_labeled_name("Byte Size Network Test")
        locust.client.post(APITasks.network_byte_size_url,  name=call_name, json=payload)


    def _small_db(locust):
        call_name = APITasks.__get_labeled_name("Small Data Base Query Network Test")
        locust.client.post(APITasks.small_db_url, name=call_name)

    def _large_db(locust):
        call_name = APITasks.__get_labeled_name("Large Data Base Query Network Test")
        locust.client.post(APITasks.large_db_url, name=call_name)

        #APITasks._get_and_validate_ts_segment(locust, ts_url, ts_content_hash)





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
        "Redundant Ts Segment": _redundant_ts_segment,
        "Basic Network": _basic_network,
        "Network Byte Size": _network_byte_size,
        "Small Data Base": _small_db,
        "Large Data Base": _large_db,


    }#TODO: FIND WAY TO MAKE VALID API ROUTES





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
        config = Config()
        pool_factory = RequestPoolFactory(config, [cls.env])
        api_base_host = config.get_api_host(cls.env)

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
                cls.update_rules_pool, cls.ur_url = pool_factory.get_update_rules_pool_and_route(cls.version, cls.env, normal_min,                                                                normal_max)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "List Rules":
                cls.list_rules_pool, cls.lr_url = pool_factory.get_list_rules_pool_and_route(cls.version, cls.env, normal_min, normal_max)
                logger.debug("Set up {0} Info".format(api_call))


            elif api_call == "Nothing":
                logger.debug("Set up {0} Info".format(api_call))


            elif api_call == "Redundant Ts Segment":
                cls.ts_segment_urls = pool_factory.get_redundant_ts_segment_urls(cls.env, normal_min)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "Basic Network":
                cls.basic_network_url = "{host}/rec/test/vip-test/".format(host = api_base_host)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "Network Byte Size":

                cls.network_byte_size_url = "{host}/rec/test/byte-size-test/".format(host=api_base_host)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "Small Data Base":
                cls.small_db_url = "{host}/rec/test/small-db-test/".format(host=api_base_host)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "Large Data Base":
                cls.large_db_url = "{host}/rec/test/big-db-test/".format(host=api_base_host)
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
            api_call_weight = cls.api_call_weight[api_call]
            if api_call_weight == 0:
                continue
            api_call_method = cls._task_method_realtion[api_call]
            for _ in range(api_call_weight):
                tasks_to_be.append(api_call_method)
        cls.tasks = tasks_to_be

        logger.debug("tasks set to {0}".format(tasks_to_be))


    @staticmethod
    def post_json_csm_copy(locust, json_info, url, name=None):
        """
        This function assumes that all requests must be under the designated max response time, close after,
        and that the resposne code must be 200
        :param locust:
        :param json_info:
        :param url:
        :return:
        """

        header = {"Content-Type": "application/json", "Connection": "close"}
        call_name = APITasks.__get_labeled_name(url) if name is None else APITasks.__get_labeled_name(name)
        locust.client.request("POST", url, name=call_name, data=json.dumps(json_info), headers=header)



    @staticmethod
    def __get_labeled_name(name):
        call_name = "{env}:{node}  -  {route}".format(env=APITasks.env, node=APITasks.node, route=name)
        return call_name

class APIUser(HttpLocust):
    """
    Locust user class that does requests to the Performance_Test web server running on localhost
    """

    min_wait = 1 * SECONDS
    max_wait = 1 * SECONDS
    task_set = APITasks








