from Load_Test.Misc.utils import merge_dicts
from Load_Test.exceptions import InvalidRoute

class RouteRelationBase(object):
    @property
    def relation(self):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        self.__raise_not_in_relation(key)
        self.relation[key] = value

    def __getitem__(self, key):
        self.__raise_not_in_relation(key)
        return self.relation[key]

    def __delitem__(self, key):
        self.__raise_not_in_relation(key)
        self.relation[key] = None




    def keys(self):
        return [getattr(self, attr) for attr in dir(self) if not callable(getattr(self, attr))
                and not attr.startswith("__")]


    def __raise_not_in_relation(self, key):
        if key not in self.keys():
            raise InvalidRoute("{key} not in acceptable keys - {keys}".format(key=key, keys=str(self.keys())))

    def execute_related(self, route, *args):
        return self[route](*args)

class APIRoutesRelation(RouteRelationBase):
    USER_RECORDING_RIBBON = "User Recordings Ribbon"
    USER_FRANCHISE_RIBBON = "User Franchise Ribbon"
    USER_RECSPACE_INFO    = "User Recspace Information"
    UPDATE_USER_SETTINGS  = "Update User Settings"
    CREATE_RECORDINGS     = "Create Recordings"
    PROTECT_RECORDINGS    = "Protect Recordings"
    MARK_WATCHED          = "Mark Watched"
    DELETE_RECORDINGS     = "Delete Recordings"
    CREATE_RULES          = "Create Recordings"
    UPDATE_RULES          = "Update Rules"
    DELETE_RULES          = "Delete Rules"
    LIST_RULES            = "List Rules"

    #these are test routes used by locust to validate other issues
    NOTHING               = "Nothing"
    REDUNDANT_TS_SEG      = "Redundant Ts Segment"
    BASIC_NETWORK         = "Basic Network"
    NETWORK_BYTE_SIZE     = "Network Byte Size"
    SMALL_DB              = "Small Db"
    LARGE_DB              = "Large Db"
    NGINX_CHECK           = "Nginx Check"

    @classmethod
    def empty_relation(cls):
        return APIRoutesRelation(None, None, None, None, None, None, None, None, None, None, None, None,
                                 None, None, None, None, None, None, None)

    @property
    def relation(self):
        return self._api_relation

    def __init__(self, user_rec_ribbon, user_franchise_ribbon, user_recspace_info, update_user_settings, create_recording,
                 protect_recordings, mark_watched, delete_recordings, create_rules, delete_rules, list_rules, update_rules,
                 nothing, redudnant_ts, basic_networ, network_byte_size, small_db, large_db, nginx_check):
        relation = {
            APIRoutesRelation.USER_RECORDING_RIBBON: user_rec_ribbon,
            APIRoutesRelation.USER_FRANCHISE_RIBBON: user_franchise_ribbon,
            APIRoutesRelation.USER_RECSPACE_INFO: user_recspace_info,
            APIRoutesRelation.UPDATE_USER_SETTINGS: update_user_settings,
            APIRoutesRelation.CREATE_RECORDINGS: create_recording,
            APIRoutesRelation.PROTECT_RECORDINGS: protect_recordings,
            APIRoutesRelation.MARK_WATCHED: mark_watched,
            APIRoutesRelation.DELETE_RECORDINGS: delete_recordings,
            APIRoutesRelation.CREATE_RULES: create_rules,
            APIRoutesRelation.UPDATE_RULES: update_rules,
            APIRoutesRelation.DELETE_RULES: delete_rules,
            APIRoutesRelation.LIST_RULES: list_rules,
            APIRoutesRelation.NOTHING: nothing,
            APIRoutesRelation.REDUNDANT_TS_SEG: redudnant_ts,
            APIRoutesRelation.BASIC_NETWORK: basic_networ,
            APIRoutesRelation.NETWORK_BYTE_SIZE: network_byte_size,
            APIRoutesRelation.SMALL_DB: small_db,
            APIRoutesRelation.LARGE_DB: large_db,
            APIRoutesRelation.NGINX_CHECK: nginx_check
        }
        self._api_relation = relation






class PlaybackRoutesRelation(RouteRelationBase):
    # Playback Routes
    Playback = "Playback"
    Top_N_Playback = "Top N Playback"

    @classmethod
    def empty_relation(cls):
        return PlaybackRoutesRelation(None, None)

    @property
    def relation(self):
        return self._playback_relation


    def __init__(self, playback, top_n_playback):
        relation = {
            PlaybackRoutesRelation.Playback: playback,
            PlaybackRoutesRelation.Top_N_Playback: top_n_playback
                    }
        self._playback_relation = relation

class RoutesRelation(APIRoutesRelation, PlaybackRoutesRelation):

    @classmethod
    def empty_relation(cls):
        return RoutesRelation(None, None, None, None, None, None, None, None, None, None, None, None,
                                 None, None, None, None, None, None, None, None)

    @property
    def relation(self):
        return self._relation

    def __init__(self, user_rec_ribbon, user_franchise_ribbon, user_recspace_info, update_user_settings, create_recording,
                 protect_recordings, mark_watched, delete_recordings, delete_rules, create_rules, list_rules, update_rules, nothing,
                 redudnant_ts, basic_networ, network_byte_size, small_db, large_db, nginx_check, playback, top_n_playback):

        APIRoutesRelation.__init__(self, user_rec_ribbon, user_franchise_ribbon, user_recspace_info, update_user_settings, create_recording,
                 protect_recordings, mark_watched, delete_recordings, create_rules, delete_rules, list_rules, update_rules,
                 nothing, redudnant_ts, basic_networ, network_byte_size, small_db, large_db, nginx_check)

        PlaybackRoutesRelation.__init__(self, playback, top_n_playback)
        self._relation = merge_dicts(self._playback_relation, self._api_relation)


