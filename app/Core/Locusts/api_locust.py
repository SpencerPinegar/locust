import json
import logging
import random
import hashlib

from locust import HttpLocust, TaskSet
import locust.stats
from requests.exceptions import RequestException
from collections import namedtuple

from app.Data.config import Config
from app.Data.request_pool import RequestPoolFactory
from app.Utils.utils import get_api_info, obtain_version_number_based_on_weight_func
from app.Utils.utils import force_route_version_to_ints
from app.Utils.route_relations import APIRoutesRelation
from app.Utils.environment_wrapper import APIEnvironmentWrapper as APIWrap

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
SECONDS = 1000
Info = namedtuple("Info", ["json", "url"])
MARK_AS_FAIL = "!FAIL!"
logger.info("IMPORTED API LOCUST SUCCESFULLY")
logging.disable(logging.CRITICAL)



# setproctitle("-LOCUST API Slave {}".format(api_wrap.slave_index))
# TODO: ADD POOLS FOR CREATE/DELETE OPERATIONS -- create/delete recordings, create/delete recording rules


class APITasks(TaskSet):
    ROUTE_DATA = APIRoutesRelation.empty_relation()

    def setup(self):
        APITasks.setup_based_on_env_vars()

    def _user_recordings_ribbon(locust):
        info = APITasks.get_json_data_and_url(APIRoutesRelation.USER_RECORDING_RIBBON)
        APITasks.post_json(locust, info.url, json_info=info.json, assume_tcp_packet_loss=APITasks.assume_tcp_loss,
                           bin_by_resp=APITasks.bin_by_resp)

    def _user_franchise_ribbon(locust):
        info = APITasks.get_json_data_and_url(APIRoutesRelation.USER_FRANCHISE_RIBBON)
        APITasks.post_json(locust, info.url, json_info=info.json, assume_tcp_packet_loss=APITasks.assume_tcp_loss,
                           bin_by_resp=APITasks.bin_by_resp)

    def _user_recspace_information(locust):
        info = APITasks.get_json_data_and_url(APIRoutesRelation.USER_RECSPACE_INFO)
        APITasks.post_json(locust, info.url, json_info=info.json, assume_tcp_packet_loss=APITasks.assume_tcp_loss,
                           bin_by_resp=APITasks.bin_by_resp)

    def _update_user_settings(locust):
        info = APITasks.get_json_data_and_url(APIRoutesRelation.UPDATE_USER_SETTINGS)
        APITasks.post_json(locust, info.url, json_info=info.json, assume_tcp_packet_loss=APITasks.assume_tcp_loss,
                           bin_by_resp=APITasks.bin_by_resp)

    def _protect_recordings(locust):
        info = APITasks.get_json_data_and_url(APIRoutesRelation.PROTECT_RECORDINGS)
        APITasks.post_json(locust, info.url, json_info=info.json, assume_tcp_packet_loss=APITasks.assume_tcp_loss,
                           bin_by_resp=APITasks.bin_by_resp)

    def _mark_watched(locust):
        info = APITasks.get_json_data_and_url(APIRoutesRelation.MARK_WATCHED)
        APITasks.post_json(locust, info.url, json_info=info.json, assume_tcp_packet_loss=APITasks.assume_tcp_loss,
                           bin_by_resp=APITasks.bin_by_resp)

    def _update_user_rules(locust):
        info = APITasks.get_json_data_and_url(APIRoutesRelation.UPDATE_RULES)
        APITasks.post_json(locust, info.url, json_info=info.json, assume_tcp_packet_loss=APITasks.assume_tcp_loss,
                           bin_by_resp=APITasks.bin_by_resp)

    def _list_user_rules(locust):
        info = APITasks.get_json_data_and_url(APIRoutesRelation.LIST_RULES)
        APITasks.post_json(locust, info.url, json_info=info.json, assume_tcp_packet_loss=APITasks.assume_tcp_loss,
                           bin_by_resp=APITasks.bin_by_resp)

    def _bind_recording(locust):
        unbound_info = random.choice(APITasks.bind_recording_data)
        bind_url = APITasks.bind_recording_url.format(host=APITasks.api_base_host, rec_guid=unbound_info.rec_guid,
                                                      sched_guid=unbound_info.sched_guid, dvr_host=unbound_info.dvr_host)
        APITasks.post_json(locust, bind_url, name="Bind URL", post_method="GET")

    def _nothing(locust):
        assert 2 + 2 == 4
        pass

    def _redundant_ts_segment(locust):
        ts_url, ts_content_hash = random.choice(APITasks.ts_segment_urls)
        ts_prefix = ts_url.split("//")[1][0].lower()
        call_name = "{env} - ts request validation".format(env=ts_prefix, url=ts_url)
        with locust.client.get(ts_url, name=call_name, catch_response=True) as response:
            try:
                response.raise_for_status()
            except RequestException as e:
                response.failure(e)
            else:
                content = response.content
                created_content_hash = hashlib.md5(str(content)).hexdigest()
                if created_content_hash != ts_content_hash:
                    response.failure("Invalid TS Segment - Expected {ex}, Created {created}".format(ex=ts_content_hash,
                                                                                                    created=created_content_hash))
                else:
                    response.success()

    def _basic_network(locust):
        APITasks.post_json(locust, APITasks.basic_network_url, name="Basic Network Test",
                           assume_tcp_packet_loss=True)

    def _network_byte_size(locust):
        payload = {
            "byte_size": "3"}  # TODO Make this configurable - ideally by allowing params to be passed in with api_call_weight
        APITasks.post_json(locust, APITasks.network_byte_size_url, json_info=payload, name="Network Byte Size",
                           assume_tcp_packet_loss=True)

    def _small_db(locust):
        APITasks.post_json(locust, APITasks.small_db_url, name="Small Data Base Query Network Test",
                           assume_tcp_packet_loss=True)

    def _large_db(locust):
        APITasks.post_json(locust, APITasks.large_db_url, name="Large Data Base Query Network Test",
                           assume_tcp_packet_loss=True)

    def _nginx_check(locust):
        APITasks.post_json(locust, APITasks.nginx_url, name="Nginx Check", assume_tcp_packet_loss=True)

    # def _create_delete_rules(locust):
    #    json_data

    _task_method_realtion = APIRoutesRelation(_user_recordings_ribbon,
                                              _user_franchise_ribbon,
                                              _user_recspace_information,
                                              _update_user_settings,
                                              None,
                                              _protect_recordings,
                                              _mark_watched,
                                              None,
                                              None,
                                              None,
                                              _list_user_rules,
                                              _bind_recording,
                                              _update_user_rules,
                                              _nothing,
                                              _redundant_ts_segment,
                                              _basic_network,
                                              _network_byte_size,
                                              _small_db,
                                              _large_db,
                                              _nginx_check)

    BENCHMARK = .25 * SECONDS
    SLOW = .5 * SECONDS
    VERY_SLOW = 1 * SECONDS
    USER_WAITING = 3 * SECONDS
    CMS_TIMEOUT = 6 * SECONDS  # TODO: make this come from test config file

    @classmethod
    def setup_based_on_env_vars(cls):
        api_wrap = APIWrap.load_env()
        logger.info(str(api_wrap))
        cls.api_info = force_route_version_to_ints(api_wrap.api_info)
        cls.env = api_wrap.env
        cls.bin_by_resp = api_wrap.bin_by_resp_time
        if cls.bin_by_resp:  # this means that you cannot bin responses and assume tcp loss (for now)
            cls.assume_tcp_loss = False
        else:
            cls.assume_tcp_loss = api_wrap.assume_tcp
        cls.node = "VIP" if api_wrap.node is 0 else api_wrap.node
        locust.stats.CSV_STATS_INTERVAL_SEC = api_wrap.stat_interval
        if api_wrap.max_rps:
            cls.min_wait = 0
            cls.max_wait = 0
        else:
            cls.min_wait = 1 * SECONDS
            cls.max_wait = 1 * SECONDS
        config = Config()
        pool_factory = RequestPoolFactory(config, api_wrap.comp_index, api_wrap.max_comp_index, api_wrap.slave_index,
                                          api_wrap.max_slave_index, 0, [cls.env])
        cls.api_base_host = config.recapi.get_host(cls.env, node=api_wrap.node)

        cls._set_tasks()

        logger.info("GOT ENV VARS AND SETUP -- CREATING DATA")
        # Create data setup functions for task method relation
        setup_relation = cls.__create_setup_relation(pool_factory)

        FuncNData = namedtuple("FuncNData", ["data", "func"])
        for api_call_name, api_call_info in cls.api_info.items():
            api_call_name = api_call_name.title()
            if api_call_name in config.recapi.routes:
                pool_factory.size = get_api_info(api_call_info.values()[0]).size
                data = pool_factory.get_route_pool_and_ribbon(api_call_name, api_call_info, cls.env)
                weight_func = obtain_version_number_based_on_weight_func(api_call_info)
                cls.ROUTE_DATA[api_call_name] = FuncNData(data, weight_func)
            else:
                setup_relation.execute_related(api_call_name)
            logger.info("Set up {0} Info".format(api_call_name))

    @classmethod
    def _set_tasks(cls):
        tasks_to_be = []
        for api_call, api_info in cls.api_info.items():
            api_call = api_call.title()
            try:
                total_weight = sum([x.weight for x in [get_api_info(x) for x in api_info.values()]])
            except TypeError:
                total_weight = get_api_info(api_info).weight
            if api_call not in APITasks._task_method_realtion.keys():
                logger.info("{0} is not a valid api call".format(api_call))

            if total_weight is 0:
                continue
            api_call_method = cls._task_method_realtion[api_call]
            for _ in range(total_weight):
                tasks_to_be.append(api_call_method)
        cls.tasks = tasks_to_be

        logger.info("tasks set to {0}".format(tasks_to_be))

    @classmethod
    def __create_setup_relation(cls, pool_factory):
        # def redudant_ts_setup(api_call_info):
        #     APITasks.ts_segment_urls = pool_factory.get_redundant_ts_segment_urls(APITasks.env, 500)
        #     logger.debug("Set up {0} Info".format(APIRoutesRelation.REDUNDANT_TS_SEG))

        def bind_recording():
            APITasks.bind_recording_url = "{host}/rec/v1/rec-bind/{dvr_host}/{rec_guid}/{sched_guid}.qvt"
            APITasks.bind_recording_data = pool_factory.get_unbound_recordings()
            logger.info("Set up {0} Info".format(APIRoutesRelation.BIND_RECORDING))

        def nothing_setup():
            pass

        def basic_network_setup():
            APITasks.basic_network_url = "{host}/rec/test/vip-test/".format(host=APITasks.api_base_host)
            logger.info("Set up {0} Info".format(APIRoutesRelation.BASIC_NETWORK))

        def network_byte_size_setup():
            APITasks.network_byte_size_url = "{host}/rec/test/byte-size-test/".format(host=APITasks.api_base_host)
            logger.info("Set up {0} Info".format(APIRoutesRelation.NETWORK_BYTE_SIZE))

        def small_data_base_setup():
            APITasks.small_db_url = "{host}/rec/test/small-db-test/".format(host=APITasks.api_base_host)
            logger.info("Set up {0} Info".format(APIRoutesRelation.SMALL_DB))

        def large_data_base_setup():
            APITasks.large_db_url = "{host}/rec/test/big-db-test/".format(host=APITasks.api_base_host)
            logger.info("Set up {0} Info".format(APIRoutesRelation.LARGE_DB))

        def nginx_check_setup():
            APITasks.nginx_url = "{host}/srv-ok".format(host=APITasks.api_base_host)

        setup_relation = APIRoutesRelation(None, None, None, None, None, None, None, None, None, None, None,
                                           bind_recording, None, nothing_setup, None, basic_network_setup,
                                           network_byte_size_setup, small_data_base_setup, large_data_base_setup,
                                           nginx_check_setup)
        return setup_relation

    @staticmethod
    def post_json(locust, url, json_info=None, name=None, assume_tcp_packet_loss=False, bin_by_resp=False, post_method="POST"):
        """
        This function assumes that all requests must be under the designated max response time, close after,
        and that the resposne code must be 200
        :param locust:
        :param json_info:
        :param url:
        :return:
        """
        header = {"Connection": "close"}
        if json_info:
            header.setdefault("Content-Type", "application/json")
        call_name = APITasks.__get_labeled_name(url) if name is None else APITasks.__get_labeled_name(name)
        if bin_by_resp:
            APITasks._bin_by_response_time_in_name(locust, url, call_name, header, json_info, post_method)
        elif assume_tcp_packet_loss:
            APITasks._assume_tcp_loss_in_name(locust, url, call_name, header, json_info, post_method)
        else:
            if json_info:
                locust.client.request(post_method, url, name=call_name, data=json.dumps(json_info), headers=header)

            else:
                locust.client.request(post_method, url, name=call_name, headers=header)

    @staticmethod
    def _assume_tcp_loss_in_name(locust, url, call_name, header, json_info, post_method="POST"):
        if json_info:
            with locust.client.request(post_method, url, name=call_name, data=json.dumps(json_info), headers=header,
                                       catch_response=True) as resp:
                if resp.locust_request_meta["response_time"] > 1000:
                    resp.locust_request_meta["name"] = "Connection Packet loss {name}".format(
                        name=resp.locust_request_meta["name"])
                    resp.success()

                elif resp.locust_request_meta["response_time"] > 200:
                    resp.locust_request_meta["name"] = "Packet loss {name}".format(
                        name=resp.locust_request_meta["name"])
                    resp.success()
                else:
                    resp.success()
        else:
            with locust.client.request(post_method, url, name=call_name, headers=header, catch_response=True) as resp:
                if resp.locust_request_meta["response_time"] > 1000:
                    resp.locust_request_meta["name"] = "Connection Packet loss {name}".format(
                        name=resp.locust_request_meta["name"])
                    resp.success()

                elif resp.locust_request_meta["response_time"] > 200:
                    resp.locust_request_meta["name"] = "Packet loss {name}".format(
                        name=resp.locust_request_meta["name"])
                    resp.success()
                else:
                    resp.success()

    @staticmethod
    def _bin_by_response_time_in_name(locust, url, call_name, header, json_info, post_method="POST"):
        if json_info:
            with locust.client.request(post_method, url, name=call_name, data=json.dumps(json_info), headers=header,
                                       catch_response=True) as resp:
                if resp.locust_request_meta["response_time"] > 150:
                    resp.locust_request_meta["name"] = "{name} {fail}".format(
                        name=resp.locust_request_meta["name"], fail=MARK_AS_FAIL)
                    resp.success()
                else:
                    resp.success()
        else:
            with locust.client.request(post_method, url, name=call_name, headers=header, catch_response=True) as resp:

                if resp.locust_request_meta["response_time"] > 150:
                    resp.locust_request_meta["name"] = "{name} {fail}".format(
                        name=resp.locust_request_meta["name"], fail=MARK_AS_FAIL)
                    resp.success()
                else:
                    resp.success()

    @staticmethod
    def __get_labeled_name(name):
        call_name = "{env}:{node}  -  {route}".format(env=APITasks.env, node=APITasks.node, route=name)
        return call_name

    @staticmethod
    def get_json_data_and_url(route):

        data_n_func = APITasks.ROUTE_DATA[route]
        get_version_func = data_n_func.func
        data = data_n_func.data
        version = get_version_func()
        pool = data[version].pool
        url = data[version].route
        json_data = pool.get_json()
        return Info(json_data, url)


class APIUser(HttpLocust):
    """
    Locust user class that does requests to the Performance_Test web server running on localhost
    """

    task_set = APITasks
