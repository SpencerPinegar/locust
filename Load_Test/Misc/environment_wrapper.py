import json
import yaml
import os
from collections import namedtuple




class EnvironmentWrapper:
    WRAP_INFO_KEY = "WRAP_OPTIONS"

    def __init__(self, env, options, update):
        os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY', 'YES')
        os.environ['no_proxy'] = '127.0.0.1,localhost,0.0.0.0'

        self.__env = env
        info = self.__env.get(EnvironmentWrapper.WRAP_INFO_KEY)
        self._options = {} if info is None else yaml.safe_load(info)
        if update:
            for key, value in options.iteritems():
                self._options[key] = value

    def __delitem__(self, key):
        return self._options.remove(key)

    def __getitem__(self, key):
        return self._options.get(key)

    def __setitem__(self, key, value):
        self._options[key] = value

    def __repr__(self):
        return_string = "\n"
        for key, value in self._options.items():
            return_string = return_string + str(key) + " " + str(value) + "\n"
        return return_string

    def __str__(self):
        return self.__repr__()

    def keys(self):
        return self._options.keys()

    def __set_env(self):
        self.__env[EnvironmentWrapper.WRAP_INFO_KEY] = json.dumps(self._options)

    def get_env(self):
        self.__env[EnvironmentWrapper.WRAP_INFO_KEY] = json.dumps(self._options)
        return self.__env

    def stamp_env(self):
        os.environ[EnvironmentWrapper.WRAP_INFO_KEY] = json.dumps(self._options)


class DistributedLocustEnvironmetWrapper(EnvironmentWrapper):
    STAT_INT_KEY = "STAT_INTERVAL"
    MAX_COMPUTER_INDEX_KEY = "MAX_COMPUTER_INDEX"
    COMPUTER_INDEX_KEY = "COMPUTER_INDEX"
    MAX_SLAVE_INDEX_KEY = "MAX_SLAVE_INDEX_KEY"
    SLAVE_INDEX_KEY = "SLAVE_INDEX"
    QUERY_SIZE_KEY = "QUERY_SIZE"


    @property
    def stat_interval(self):
        return self[DistributedLocustEnvironmetWrapper.STAT_INT_KEY]

    @property
    def slave_index(self):
        return self[DistributedLocustEnvironmetWrapper.SLAVE_INDEX_KEY]

    @slave_index.setter
    def slave_index(self, value):
        self[DistributedLocustEnvironmetWrapper.SLAVE_INDEX_KEY] = value

    @property
    def comp_index(self):
        return self[DistributedLocustEnvironmetWrapper.COMPUTER_INDEX_KEY]

    @comp_index.setter
    def comp_index(self, value):
        self[DistributedLocustEnvironmetWrapper.COMPUTER_INDEX_KEY] = value

    @property
    def max_slave_index(self):
        return self[DistributedLocustEnvironmetWrapper.MAX_SLAVE_INDEX_KEY]

    @max_slave_index.setter
    def max_slave_index(self, value):
        self[DistributedLocustEnvironmetWrapper.MAX_SLAVE_INDEX_KEY] = value

    @property
    def max_comp_index(self):
        return self[DistributedLocustEnvironmetWrapper.MAX_COMPUTER_INDEX_KEY]

    @property
    def size(self):
        return self[DistributedLocustEnvironmetWrapper.QUERY_SIZE_KEY]

    @size.setter
    def size(self, value):
        self[DistributedLocustEnvironmetWrapper.QUERY_SIZE_KEY] = value

    def __init__(self, stat_interval, computer_index, loc_slave_index, max_comp_index, max_loc_slave_index, size, update,
                 **kwargs):
        options = {
            DistributedLocustEnvironmetWrapper.STAT_INT_KEY: stat_interval,
            DistributedLocustEnvironmetWrapper.COMPUTER_INDEX_KEY: computer_index,
            DistributedLocustEnvironmetWrapper.SLAVE_INDEX_KEY: loc_slave_index,
            DistributedLocustEnvironmetWrapper.MAX_COMPUTER_INDEX_KEY: max_comp_index,
            DistributedLocustEnvironmetWrapper.MAX_SLAVE_INDEX_KEY: max_loc_slave_index,
            DistributedLocustEnvironmetWrapper.QUERY_SIZE_KEY: size,
        }
        for key, item in kwargs.items():
            options[key] = item
        EnvironmentWrapper.__init__(self, os.environ.copy(), options, update)
        self.get_env()

class APIEnvironmentWrapper(DistributedLocustEnvironmetWrapper):
    API_INFO_KEY = "API_INFO"
    NODE_KEY = "NODE"
    ENV_KEY = "ENV"
    MAX_RPS_KEY = "MAX_RPS"
    ASSUME_TCP_KEY = "ASSUME_TCP"
    BIN_RSP_TIME_KEY = "BIN_BY_RESP_TIME"

    @classmethod
    def load_env(cls):
        return APIEnvironmentWrapper(None, None, None, None, None, None, None, None, None, None, None, None, False)

    @property
    def api_info(self):
        return self[APIEnvironmentWrapper.API_INFO_KEY]

    @property
    def node(self):
        return self[APIEnvironmentWrapper.NODE_KEY]

    @property
    def env(self):
        return self[APIEnvironmentWrapper.ENV_KEY]

    @property
    def max_rps(self):
        return self[APIEnvironmentWrapper.MAX_RPS_KEY]

    @property
    def assume_tcp(self):
        return self[APIEnvironmentWrapper.ASSUME_TCP_KEY]

    @property
    def bin_by_resp_time(self):
        return self[APIEnvironmentWrapper.BIN_RSP_TIME_KEY]

    def __init__(self, api_info, node, env, max_rps, assume_tcp, bin_by_resp,
                 stat_int, computer_index, loc_slave_index, max_comp_index, max_loc_slave_index, size, update=True):
        options = {
           APIEnvironmentWrapper.API_INFO_KEY: api_info,
           APIEnvironmentWrapper.NODE_KEY: node,
           APIEnvironmentWrapper.ENV_KEY: env,
           APIEnvironmentWrapper.MAX_RPS_KEY: max_rps,
           APIEnvironmentWrapper.ASSUME_TCP_KEY: assume_tcp,
           APIEnvironmentWrapper.BIN_RSP_TIME_KEY: bin_by_resp
        }
        DistributedLocustEnvironmetWrapper.__init__(self, stat_int, computer_index, loc_slave_index,
                                                    max_comp_index, max_loc_slave_index, size, update, **options)


class PlaybackEnvironmentWrapper(DistributedLocustEnvironmetWrapper):
    ACTION_KEY = "ACTION"
    QUALITY_KEY = "QUALITY"
    CODECS_KEY = "CODECS"
    CLIENT_KEY = "CLIENT"
    USERS_KEY = "USERS"
    DVR_KEY = "DVR"
    DAYS_KEY = "DAYS"

    @classmethod
    def load_env(cls):
        return PlaybackEnvironmentWrapper(None, None, None, None, None, None, None, None, None, None, None, None, None, False)

    @property
    def action(self):
        return self[PlaybackEnvironmentWrapper.ACTION_KEY]

    @property
    def codecs(self):
        return self[PlaybackEnvironmentWrapper.CODECS_KEY]

    @property
    def quality(self):
        return self[PlaybackEnvironmentWrapper.QUALITY_KEY]

    @property
    def client(self):
        return self[PlaybackEnvironmentWrapper.CLIENT_KEY]

    @property
    def user(self):
        return self[PlaybackEnvironmentWrapper.USERS_KEY]

    @property
    def dvr(self):
        return self[PlaybackEnvironmentWrapper.DVR_KEY]

    @property
    def days(self):
        return self[PlaybackEnvironmentWrapper.DAYS_KEY]

    def __init__(self, action, quality, codecs, client, users, dvr, days,
                 stat_int, computer_index, loc_slave_index, max_comp_index, max_loc_slave_index, size, update=True):
       options = {
           PlaybackEnvironmentWrapper.ACTION_KEY: action,
           PlaybackEnvironmentWrapper.QUALITY_KEY: quality,
           PlaybackEnvironmentWrapper.CODECS_KEY: codecs,
           PlaybackEnvironmentWrapper.CLIENT_KEY: client,
           PlaybackEnvironmentWrapper.USERS_KEY: users,
           PlaybackEnvironmentWrapper.DVR_KEY: dvr,
           PlaybackEnvironmentWrapper.DAYS_KEY: days
       }
       DistributedLocustEnvironmetWrapper.__init__(self, stat_int, computer_index, loc_slave_index, max_comp_index,
                                                   max_loc_slave_index, size, update, **options)


