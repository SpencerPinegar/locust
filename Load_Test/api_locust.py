from locust import HttpLocust, TaskSet, create_options, run_locust
from Load_Test.request_pool import RequestPoolFactory
from Load_Test.Config.config import Config
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)



# TODO: ADD POOLS FOR CREATE/DELETE OPERATIONS -- create/delete recordings, create/delete recording rules



class APITasks(TaskSet):

    def _user_recordings_ribbon(locust):
        json_data = APITasks.user_recordings_pool.get_json()
        locust.client.post(APITasks.urr_url, json=json_data)



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

    _task_method_realtion = {
        "User Recordings Ribbon": _user_recordings_ribbon,
        "User Franchise Ribbon": _user_franchise_ribbon,
        "User Recspace Information": _user_franchise_ribbon,
        "Update User Settings": _update_user_settings,
        "Protect Recordings": _protect_recordings,
        "Mark Watched": _mark_watched,
        "Update Rules": _update_user_rules,
        "List Rules": _list_user_rules,
    }

    @classmethod
    def init_data(cls, api_call_weight, pool_factory, version, env, normal_min, normal_max):
        """
        :param api_call_weight:
        :param pool_factory:
        :param version:
        :param env:
        :param normal_min:
        :param normal_max:
        :return:
        """
        for api_call in api_call_weight.keys():
            if api_call == "User Recordings Ribbon":
                cls.user_recordings_pool, cls.urr_url = pool_factory.get_user_recordings_ribbon_pool_and_route(version, env,
                                                                                                       normal_min,
                                                                                                       normal_max)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "User Franchise Ribbon":
                cls.user_franchise_pool, cls.ufr_url = pool_factory.get_user_franchise_ribbon_pool_and_route(version, env,
                                                                                                             normal_min,
                                                                                                             normal_max)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "User Recspace Information":
                cls.user_recspace_info_pool, cls.uri_url = pool_factory.get_user_recspace_information_pool_and_route(version,
                                                                                                             env,
                                                                                                             normal_min,
                                                                                                             normal_max)
                logger.debug("Set up {0} Info".format(api_call))

            elif api_call == "Update User Settings":
                cls.update_user_settings_pool, cls.uus_url = pool_factory.get_update_user_settngs_pool_and_route(version, env,
                                                                                                         normal_min,
                                                                                                         normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            elif api_call == "Protect Recordings":
                cls.protect_recordings_pool, cls.pr_url = pool_factory.get_protect_recordings_pool_and_route(version, env,
                                                                                                     normal_min,
                                                                                                     normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            elif api_call == "Mark Watched":
                cls.marked_watched_pool, cls.mw_url = pool_factory.get_mark_watched_pool_and_route(version, env, normal_min,
                                                                                           normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            elif api_call == "Update Rules":
                cls.update_rules_pool, cls.ur_url = pool_factory.get_update_rules_pool_and_route(version, env, normal_min,
                                                                                         normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            elif api_call == "List Rules":
                cls.list_rules_pool, cls.lr_url = pool_factory.get_list_rules_pool_and_route(version, env, normal_min, normal_max)
                logger.debug("Set up {0} Info".format(api_call))
            else:
                logger.error("{0} is not a valid API call - valid api calls {1}".format(api_call, APITasks._task_method_realtion.keys()))



    @classmethod
    def set_tasks(cls, api_call_weight):
        tasks_to_be = []
        for api_call in api_call_weight.keys():
            api_call = api_call.title()
            if api_call not in APITasks._task_method_realtion.keys():
                logger.error("{0} is not a valid api call".format(api_call))
            for add_task_count in range(api_call_weight[api_call]):
                tasks_to_be.append(APITasks._task_method_realtion[api_call])
        cls.tasks = tasks_to_be
        logger.debug("tasks set to {0}".format(tasks_to_be))



class APIUser(HttpLocust):
    """
    Locust user class that does requests to the locust web server running on localhost
    """

    min_wait = 0
    max_wait = 0
    task_set = APITasks


def run_programmatically(api_call_weight, env, node, version, min, max, num_clients, hatchrate, runtime, **kwargs):

    config = Config()
    pool_factory = RequestPoolFactory(config)
    host = config.get_api_host(env, node)
    APITasks.init_data(api_call_weight, pool_factory, version, env, min, max)
    APITasks.set_tasks(api_call_weight)
    options = create_options(locust_classes=[APIUser], host=host, no_web=True, num_clients=num_clients, hatch_rate=hatchrate,
                             loglevel="WARNING", run_time=runtime, **kwargs)
    run_locust(options)




