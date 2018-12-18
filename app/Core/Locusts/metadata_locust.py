import json
import logging
import random
import hashlib

from locust import HttpLocust, TaskSet, seq_task, task
import locust.stats
from requests.exceptions import RequestException
from collections import namedtuple

from app.Data.config import Config
from app.Data.request_pool import RequestPoolFactory
from app.Utils.utils import get_api_info, obtain_version_number_based_on_weight_func
from app.Utils.utils import force_route_version_to_ints
from app.Utils.route_relations import MetaDataRelation
from app.Utils.environment_wrapper import MetaDataEnvironmentWrapper as MDWrap

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
SECONDS = 1000
Info = namedtuple("Info", ["json", "url"])
MARK_AS_FAIL = "!FAIL!"
logger.info("IMPORTED MetaData LOCUST SUCCESFULLY")
#logging.disable(logging.CRITICAL)

load_asset_weight = 10
get_asset_json_weight = 50
get_asset_jpeg_weight = 200

load_airing_weight = 10
get_airing_jpeg_weight = 200

# setproctitle("-LOCUST API Slave {}".format(api_wrap.slave_index))
# TODO: ADD POOLS FOR CREATE/DELETE OPERATIONS -- create/delete recordings, create/delete recording rules

class MetaDataAiringTasks(TaskSet):

    def setup(self):
        MetaDataAiringTasks.setup_based_on_env_vars()

    @seq_task(1)
    @task(1)
    def _load_all_schedules(locust):
        while MetaDataAiringTasks.UnloadedAssets:
            asset = MetaDataAiringTasks.UnloadedAssets.pop()
            MetaDataAiringTasks.post_json(locust, MetaDataAiringTasks.LoadAssetURL, post_method="PUT")
            sched_guids = asset.get("schedule")
            for sched in sched_guids:
                MetaDataAiringTasks.LoadedAssets.append(sched)

    @seq_task(2)
    @task(10)
    def _get_asset_json(locust):
        sched_guid = random.choice(MetaDataAiringTasks.LoadedAssets)
        url = MetaDataAiringTasks.GetAssetJSONURL.format(sched_guid = sched_guid)
        MetaDataAiringTasks.post_json(locust, url, name="Get Asset Json", post_method="GET")




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
        call_name = MetaDataAiringTasks.__get_labeled_name(url) if name is None else MetaDataAiringTasks.__get_labeled_name(name)
        if bin_by_resp:
            MetaDataAiringTasks._bin_by_response_time_in_name(locust, url, call_name, header, json_info, post_method)
        elif assume_tcp_packet_loss:
            MetaDataAiringTasks._assume_tcp_loss_in_name(locust, url, call_name, header, json_info, post_method)
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
        call_name = "{env}:{node}  -  {route}".format(env=MetaDataAiringTasks.env, node=MetaDataAiringTasks.node, route=name)
        return call_name


class MetaDataAssetTasks(TaskSet):

    @seq_task(1)
    def _load_all_schedules(locust):
        while MetaDataAssetTasks.UnloadedAssets.pool:
            asset = MetaDataAssetTasks.UnloadedAssets.pool.pop()
            MetaDataAssetTasks.post_json(locust, MetaDataAssetTasks.UnloadedAssets.route, json_info=asset,
                                         post_method="PUT")
            sched_guids = asset.get("schedule")
            for sched in sched_guids:
                MetaDataAssetTasks.LoadedAssets.append(sched)

    @seq_task(2)
    @task(10)
    def _get_asset_json(locust):
        if not MetaDataAssetTasks.LoadedAssets:
            return
        sched_guid = random.choice(MetaDataAssetTasks.LoadedAssets)
        url = MetaDataAssetTasks.GetAssetJSONURL.format(sched_guid = sched_guid)
        MetaDataAssetTasks.post_json(locust, url, name="Get Asset Json", post_method="GET")

    @seq_task(3)
    @task(200)
    def _get_asset_jpeg(locust):
        if not MetaDataAssetTasks.LoadedAssets:
            return
        sched_guid = random.choice(MetaDataAssetTasks.LoadedAssets)
        url = MetaDataAssetTasks.GetAssetJSONURL.format(sched_guid = sched_guid)
        MetaDataAssetTasks.post_json(locust, url, name="Get Asset Jpeg", post_method="GET")



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
        call_name = MetaDataAssetTasks.__get_labeled_name(url) if name is None else MetaDataAssetTasks.__get_labeled_name(name)
        if bin_by_resp:
            MetaDataAssetTasks._bin_by_response_time_in_name(locust, url, call_name, header, json_info, post_method)
        elif assume_tcp_packet_loss:
            MetaDataAssetTasks._assume_tcp_loss_in_name(locust, url, call_name, header, json_info, post_method)
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
        call_name = "{env}:{node}  -  {route}".format(env=MetaDataAssetTasks.env, node=MetaDataAssetTasks.node, route=name)
        return call_name



class MetaDataUser(HttpLocust):
    """
    Locust user class that does requests to the Performance_Test web server running on localhost
    """
    def setup(self):
        MetaDataUser.setup_based_on_env_vars()

    @classmethod
    def setup_based_on_env_vars(cls):
        try:
            api_wrap = MDWrap.load_env()
            logger.info(str(api_wrap))
            action = api_wrap.api_info
            config = Config()
            pool_factory = RequestPoolFactory(config, api_wrap.comp_index, api_wrap.max_comp_index,
                                              api_wrap.slave_index,
                                              api_wrap.max_slave_index, 0, [api_wrap.env])
            api_config = getattr(config, api_wrap.api_service_name)
            api_base_host = api_config.get_host(api_wrap.env, node=api_wrap.node)
            cls.host = api_base_host
            if action == "Asset":
                cls.task_set = MetaDataAssetTasks
                MetaDataAssetTasks.UnloadedAssets = pool_factory.get_load_asset({1: {"norm_lower": api_wrap.put_size,
                                                                                     "optional_fields": {},
                                                                                     "norm_upper": api_wrap.put_size,
                                                                                     "weight": 1,
                                                                                     "size": api_wrap.size}},
                                                                                api_wrap.env)[1]
                MetaDataAssetTasks.LoadedAssets = []
                MetaDataAssetTasks.LoadAssetURL = api_base_host + api_config.get_route(MetaDataRelation.LOAD_ASSET, 1)
                MetaDataAssetTasks.GetAssetJSONURL = api_base_host + api_config.get_route(
                    MetaDataRelation.GET_ASSET_JSON, 1)
                MetaDataAssetTasks.GetAssetJPEGURL = api_base_host + api_config.get_route(
                    MetaDataRelation.GET_ASSET_JPEG, 1)
                MetaDataAssetTasks.env = api_wrap.env
                MetaDataAssetTasks.node = "VIP" if api_wrap.node is 0 else api_wrap.node
            else:
                cls.task_set = MetaDataAiringTasks
            MetaDataAssetTasks.env = api_wrap.env
            cls.node = "VIP" if api_wrap.node is 0 else api_wrap.node
            locust.stats.CSV_STATS_INTERVAL_SEC = api_wrap.stat_interval
            cls.min_wait = 1 * SECONDS
            cls.max_wait = 1 * SECONDS
        except Exception as e:
            print(e)
    task_set = MetaDataAssetTasks

