import logging
import random
import sys
import json
import requests
import hashlib

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)


class RequestPoolFactory:
    """
    Read-Only API's - These API's are functional and do not require a state change - they are simply called with real data

        - User Recordings
        - User Franchise
        - List Rules
        - Mark Watched

    Two-State API's - These API's must change a field in a database row to work, So we grab data in the assumed state,
                           change it to the First state, then revert it to the last state so no real changes are made

        - Protect Recordings
            Assumed State ~ protected = True
            First state ~ protected = False
            Last state ~ protected = True

        - Update Recording Rules
            Assumed State ~ mode = 1 (all)
            First state ~ mode = 2 (new)
            Last state ~ mode = 1 (all)

    Inverse API's - These API's must add/remove a row in a database to work. To accomidate this test users are used
                        created/deleted data is tracked while the test is run ~ at shut down

        - Create/Delete Recordings
        - Create/Delete Recordings Rules
    """

    def __init__(self, config, envs=None):
        self.config = config
        self.env_db_connections = self._init_connections(envs)

    def get_user_recordings_ribbon_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "User Recordings Ribbon"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    def get_user_franchise_ribbon_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "User Franchise Ribbon"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    def get_user_recspace_information_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "User Recspace Information"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    def get_update_user_settngs_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        start_params = {"rs_recspace": 80085}
        end_params = {"rs_recspace": 599}
        route_name = "Update User Settings"
        pool = self._get_two_state_pool(route_name, version, env, start_params, end_params, min_pool_size,
                                        max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    # TODO: CREATE RECORDINGS HERE

    def get_protect_recordings_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        start_params = {"protected": False}
        end_params = {"protected": True}
        route_name = "Protect Recordings"
        pool = self._get_two_state_pool(route_name, version, env, start_params, end_params, min_pool_size,
                                        max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    def get_mark_watched_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "Mark Watched"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    # TODO: DELETE Recordings

    # TODO: Create Rules Here

    def get_update_rules_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        start_params = {"mode": "all"}
        end_params = {"mode": "new"}
        route_name = "Update Rules"
        pool = self._get_two_state_pool(route_name, version, env, start_params, end_params, min_pool_size,
                                        max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    # TODO: DELETE RULES HERE

    def get_list_rules_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "List Rules"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route


    def get_redundant_ts_segment_urls(self, env, size, **kwargs):
        ts_hosts = ["http://p-dc10-dvrmfs-2122.rp.movetv.com/a1093a971dd24afd8a75ecc72025910b/a2b88f28919411e8bd4c0025b5472111/5db4cfcedce811e7a824124234136d4e/p0500006740.ts",
                   "http://d-gp2-dvrmfs-1124.rd.movetv.com/be275c33fe5947c494e7e65b3c5e5a89/0c756d68918211e8b9630025b5472210/6c48edbedb6b11e78e3900505697cbbf/p09000025a0.ts",
                    "http://d-gp2-dvrmfs-1123.rd.movetv.com/58de947979af4b81bc31dd243d71e6af/48b31b9e995d11e882500025b5472115/5eac943aba8711e7b74e0a3e7092b342/p0500004b30.ts",
                    "http://d-gp2-dvrmfs-1122.rd.movetv.com/0ddd0ba4dd18460f98ce905087b62746/79bc40e6956e11e89d960025b5471211/2e65e682ba8711e7b6fb0a34fb89c4bc/p0500003980.ts"
                   ]
        return_stream = {}
        for ts_host in ts_hosts:
            ts_request = requests.get(ts_host)
            if ts_request.status_code != 200:
                assert False is True #


            ts_hash = hashlib.md5(str(ts_request.content)).hexdigest()
            return_stream.setdefault(ts_host, ts_hash)
        return list(return_stream.items())
        # route_name = "Redundant Ts Segment"
    #         # conn = self._get_connection(env)
    #         # querry = self.config.get_function_querry(route_name)
    #         # try:
    #         #     with conn.cursor() as cur:
    #         #         cur.execute(querry)
    #         #         data = cur.fetchall()
    #         #         self.max_pool_size = len(data)
    #         #
    #         # except Exception as e:
    #         #     logger.exception(e)
    #         #     sys.exit(1)
    #         # else:
    #         #     logger.info("Got QVT")
    #         #     qvt_host = data[0][0]
    #         #     qvt_response = requests.get(qvt_host)
    #         #     if qvt_response.status_code != 200:
    #         #         logger.error("Could not reach QVT Resource {qvt}".format(qvt=qvt_host))
    #         #     qvt_json = json.loads(qvt_response.content)
    #         #     m3u8_host = qvt_json[u"playback_info"][u"m3u8_url_template"]
    #         #     m3u8_host = m3u8_host.replace("$encryption_type$", "internal")
    #         #     m3u8_resposne = requests.get(m3u8_host)
    #         #     if m3u8_resposne.status_code != 200:
    #         #         logger.error("Could not reach M3U8 Resource {M3U8}".format(M3U8=m3u8_host))
    #         #     m3u8_manifest = m3u8_resposne.content
    #         #     for line in m3u8_manifest.splitlines():
    #         #         if line.startswith("#"):
    #         #             continue
    #         #         else:100
    #         #             stream = line
    #         #             break
    #         #
    #         #     stream_host = m3u8_host.replace("internal_master.m3u8", stream)
    #         #     stream_response = requests.get(stream_host)
    #         #     if stream_response.status_code != 200:
    #         #         logger.error("Could not reach Stream Resource {stream}".format(stream=stream_host))
    #         #     stream_content = stream_response.content
    #         #     return_streams = {}
    #         #     for line in stream_content.splitlines():
    #         #         if line.startswith("#"):
    #         #             continue
    #         #         elif line.endswith(".ts"):
    #         #             ts_host = m3u8_host.replace("internal_master.m3u8", line)
    #         #             ts_response = requests.get(ts_host)
    #         #             if ts_response.status_code != 200:
    #         #                 logger.error("Could not reach Ts Segement {ts}".format(ts=ts_host))
    #         #             else:
    #         #                 ts_content = ts_response.content
    #         #                 ts_hash = hashlib.md5(str(ts_content)).hexdigest()
    #         #                 return_streams.setdefault(ts_host, ts_hash)
    #         #                 if len(return_streams) is size:
    #         #                     return list(return_streams.items())
    #         #     logger.error("Could Not find enough ts Segments")

    # TODO: Create Functions To get Create/Delete Request Pools

    def _get_route(self, route, version):
        return self.config.get_api_route(route, version)

    def _get_pool(self, route, version, env, min_pool_size, max_pool_size, **kwargs):

        sql_route, req_fields, opt_fields, min_norm, max_norm, is_list = self._get_route_version_info(route, version)
        datapool = _ReadOnlyRequestPool(sql_route, req_fields, opt_fields, min_norm, max_norm, is_list, min_pool_size,
                                        max_pool_size)
        datapool.init_normal_pool(self._get_connection(env), **kwargs)
        return datapool

    def _get_two_state_pool(self, route, version, env, start_params, end_params, min_pool_size, max_pool_size,
                            **kwargs):
        sql_route, req_fields, opt_fields, min_norm, max_norm, is_list = self._get_route_version_info(route, version)
        datapool = _TwoStateRequestPool(sql_route, req_fields, opt_fields, min_norm, max_norm, start_params, end_params,
                                        is_list, min_pool_size, max_pool_size)
        datapool.init_normal_pool(self._get_connection(env), **kwargs)
        return datapool

    def _init_connections(self, envs):
        connections = {}
        if envs is not None:
            for env in envs:
                connections.setdefault(env, self.config.get_db_connection(env))
            return connections
        else:
            for env in self.config.get_db_environments():
                connections.setdefault(env, self.config.get_db_connection(env))
            return connections

    def _get_connection(self, env):
        return self.env_db_connections[env]

    def _get_route_version_info(self, route, version):
        sql_route, versions_info, min_norm, max_norm, is_list = self.config.get_api_route_specs(route)
        version = versions_info[version]
        req_fields = version["Required Fields"]
        opt_fields = version["Optional Fields"]
        return sql_route, req_fields, opt_fields, min_norm, max_norm, is_list




    def close(self):
        for value in self.env_db_connections.values():
            value.close()

    # TODO:: Create Pool Class for Create/Delete API's; Create-Delete-Recordings, Create-Delete-Recording-Rules


class _ReadOnlyRequestPool(object):

    # TODO:: Make the a method to verify data/responses

    def __init__(self, sql, req_fields, opt_fields, min, max, is_list, min_pool_size, max_pool_size):

        self.is_list = is_list
        self.normal_min = -1 if min == None else min
        self.normal_max = -1 if max == None else max
        self.required_fields = req_fields
        self.optional_fields = opt_fields
        self.max_pool_size = -1
        self.normal_data = True
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._set_SQL(sql)
        self.normal_pool = None




    def add_optional_defualt_params(self, **kwargs):
        for key, value in kwargs.iteritems():
            if not self._is_optional_request_param(key, value):
                logger.error("Invalid default Params")
                return
        for key, value in kwargs.iteritems():
            for item in self.normal_pool:
                item.setdefault(key, value)

    def get_json(self, **kwargs):
        if not self._is_succesful_init():
            logger.error("Random JSON returned is None because no data could be found")
            return

        json = random.choice(self.normal_pool)
        if kwargs is not None:
            return_json = {}
            for key, value in kwargs.iteritems():
                if self._is_optional_request_param(key, value):
                    return_json.setdefault(key, value)
            return_json.update(json)
            return self._listify(return_json)
        else:
            return self._listify(json)

    def init_normal_pool(self, conn, min=-1, max=-1, **kwargs):
        if self.max_pool_size <= 10 and self.max_pool_size != -1:
            logger.debug("Max Pool Size = {0}, There may not be enough normal data to accuratly load test".format(
                self.max_pool_size))
        if min and max == -1:
            min = self.normal_min
            max = self.normal_max
        real_normal_request_data = self._get_normal_request_data(conn, min, max)
        default_dict = {}
        if kwargs is not None:
            for key, value in kwargs.iteritems():
                default_dict.setdefault(key, value)
        real_normal_json_data = self._proccess_normal_request_data(real_normal_request_data, default_dict)
        self.normal_pool = real_normal_json_data

    def _is_succesful_init(self):
        if self.max_pool_size == -1:
            logger.error("normal pool must be initialized prior to getting data")
            return False
        if len(self.normal_pool) < self.min_pool_size:
            logger.error("Your pool was size was {0}: The minimum pool size is {1} - Create more data".format(
                len(self.normal_pool), self.min_pool_size))
            return False
        return True

    def _set_SQL(self, SQL):
        SQL = SQL.lower()
        if self.normal_min and self.normal_max == -1:
            head, part, tail = SQL.partition("having")
            self._SQL = head + " limit {limit}"
            self.normal_data = False
        elif SQL.__contains__("{min}") and SQL.__contains__("{max}"):
            self._SQL = SQL + " limit {limit}"
            self.normal_data = True
        else:
            logger.error("The SQL Statement entered is invalid - it must contain a Having condition based"
                         "on expected normal minimums and maximums variables; {0} = min and {1} = max")
            sys.exit(-1)

    def _get_normal_request_data(self, conn, min, max):
        sql_var_dict = {"min": min, "max": max, "limit": self.max_pool_size}
        for value in self.required_fields.values():
            if isinstance(value, dict):
                for arg_name, arg_val in value.iteritems():
                    if isinstance(arg_name, str) and arg_name.startswith("arg"):
                        sql_var_dict.setdefault(arg_name, arg_val)

        querry = self._SQL.format(**sql_var_dict)
        try:
            with conn.cursor() as cur:
                cur.execute(querry)
                data = cur.fetchall()
                self.max_pool_size = len(data)

        except Exception as e:
            logger.exception(e)
            sys.exit(1)
        else:
            return data

    def _proccess_normal_request_data(self, normal_data, default_dict=None):
        if default_dict is None:
            default_dict = dict()
        json_data = []
        for key, value in self.required_fields.iteritems():
            if isinstance(value, list):
                default_dict.setdefault(key, value[0])
        for normal_row in normal_data:
            json = {}
            for key, value in self.required_fields.iteritems():
                if "pos" in value:
                    position = value["pos"]
                    json.setdefault(key, normal_row[position])
            json.update(**default_dict)
            json_data.append(json)

        return json_data

    def _is_optional_request_param(self, key, value):

        if key not in self.optional_fields:
            logger.error("{0} is not an accepted argument for this request; Accepted arguments {1}".format(key,
                                                                                                           self.optional_fields))
            return False
        key_values = self.optional_fields[key]
        if isinstance(key_values, list) and value not in key_values:
            logger.error(
                "{0} is not an acceted value for the key {1}. Accepted arguemnts for {1}: {2}".format(value, key,
                                                                                                      key_values))
            return False
        return True

    def _is_empty(self, attr):
        """
        A quick helper method to verify that inputs for the user recordings json are empty
        :param attr:
        :return:
        """
        if attr == "" or attr == None:
            return True
        else:
            return False

    def clean_optional_params(self):
        if self._is_succesful_init():
            remove = [x for x in self.normal_pool[0].keys() if x not in self.required_fields.keys()]
            for json in self.normal_pool:
                for to_be_removed in remove:
                    json.pop(to_be_removed)

    def _listify(self, json):
        if self.is_list:
            return [json]
        else:
            return json


class _TwoStateRequestPool(_ReadOnlyRequestPool):

    def __init__(self, sql, req_fields, opt_fields, min, max, start_state_params, end_state_params, is_list,
                 min_pool_size, max_pool_size):
        _ReadOnlyRequestPool.__init__(self, sql, req_fields, opt_fields, min, max, is_list, min_pool_size,
                                      max_pool_size)
        self.index = 0
        self.start_state_params = start_state_params
        self.end_state_params = end_state_params
        self.current_default_params = start_state_params

    def get_json(self, **kwargs):
        if not self._is_succesful_init():
            logger.error("JSON return is None because no data could be found")
            return
        try:
            json = self.normal_pool[self.index]
            self.index += 1
            return self._listify(json)
        except IndexError as e:
            self.flip_state()
            return self.get_json()

    def _proccess_normal_request_data(self, normal_data, default_dict=None):
        if default_dict is None:
            default_dict = dict()
        default_dict.update(**self.current_default_params)
        return super(_TwoStateRequestPool, self)._proccess_normal_request_data(normal_data, default_dict)

    def flip_state(self):
        self.index = 0
        self.clean_optional_params()
        if self.current_default_params is self.start_state_params:
            self.current_default_params = self.end_state_params
            self.add_optional_defualt_params(**self.current_default_params)
        else:
            self.current_default_params = self.start_state_params
            self.add_optional_defualt_params(**self.current_default_params)

    def close(self, url):
        self.clean_optional_params()
        self.current_default_params = self.end_state_params
        self.add_optional_defualt_params(**self.current_default_params)
        for json in self.normal_pool:
            to_send = self._listify(json)
            response = requests.post(url, json=to_send)
            assert response.status_code in [200, 404]


class _InverseStateRequestPool(_ReadOnlyRequestPool):
    pass
