from app.Utils.utils import merge_dicts
from app.Core.exceptions import InvalidRoute

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


class MetaDataRelation(RouteRelationBase):
    GET_ASSET_JSON = "Get Asset Json"
    GET_ASSET_JPEG = "Get Asset Jpeg"
    LOAD_ASSET     = "Load Asset"
    GET_AIRING     = "Get Airing"
    LOAD_AIRING    = "Load Airing"

    @classmethod
    def empty_relation(cls):
        return MetaDataRelation(None, None, None, None, None)

    @property
    def relation(self):
        return self._metadata_relation

    def __init__(self, get_asset_json, get_asset_jpeg, load_asset, get_airing, load_airing):
        relation = {
            MetaDataRelation.GET_ASSET_JSON: get_asset_json,
            MetaDataRelation.GET_ASSET_JPEG: get_asset_jpeg,
            MetaDataRelation.LOAD_ASSET:     load_asset,
            MetaDataRelation.GET_AIRING:     get_airing,
            MetaDataRelation.LOAD_AIRING:    load_airing,
        }
        self._metadata_relation = relation

class RecAPIRoutesRelation(RouteRelationBase):
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
    BIND_RECORDING        = "Bind Recording"

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
        return RecAPIRoutesRelation(None, None, None, None, None, None, None, None, None, None, None, None,
                                    None, None, None, None, None, None, None, None)

    @property
    def relation(self):
        return self._recapi_relation

    def __init__(self, user_rec_ribbon, user_franchise_ribbon, user_recspace_info, update_user_settings, create_recording,
                 protect_recordings, mark_watched, delete_recordings, create_rules, delete_rules, list_rules, bind_rec,
                 update_rules, nothing, redudnant_ts, basic_networ, network_byte_size, small_db, large_db, nginx_check):
        relation = {
            RecAPIRoutesRelation.USER_RECORDING_RIBBON: user_rec_ribbon,
            RecAPIRoutesRelation.USER_FRANCHISE_RIBBON: user_franchise_ribbon,
            RecAPIRoutesRelation.USER_RECSPACE_INFO: user_recspace_info,
            RecAPIRoutesRelation.UPDATE_USER_SETTINGS: update_user_settings,
            RecAPIRoutesRelation.CREATE_RECORDINGS: create_recording,
            RecAPIRoutesRelation.PROTECT_RECORDINGS: protect_recordings,
            RecAPIRoutesRelation.MARK_WATCHED: mark_watched,
            RecAPIRoutesRelation.DELETE_RECORDINGS: delete_recordings,
            RecAPIRoutesRelation.CREATE_RULES: create_rules,
            RecAPIRoutesRelation.UPDATE_RULES: update_rules,
            RecAPIRoutesRelation.DELETE_RULES: delete_rules,
            RecAPIRoutesRelation.LIST_RULES: list_rules,
            RecAPIRoutesRelation.BIND_RECORDING: bind_rec,
            RecAPIRoutesRelation.NOTHING: nothing,
            RecAPIRoutesRelation.REDUNDANT_TS_SEG: redudnant_ts,
            RecAPIRoutesRelation.BASIC_NETWORK: basic_networ,
            RecAPIRoutesRelation.NETWORK_BYTE_SIZE: network_byte_size,
            RecAPIRoutesRelation.SMALL_DB: small_db,
            RecAPIRoutesRelation.LARGE_DB: large_db,
            RecAPIRoutesRelation.NGINX_CHECK: nginx_check
        }
        self._recapi_relation = relation






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

class RoutesRelation(MetaDataRelation, RecAPIRoutesRelation, PlaybackRoutesRelation):

    @classmethod
    def empty_relation(cls):
        return RoutesRelation(None, None, None, None, None, None, None, None, None, None, None, None,
                                 None, None, None, None, None, None, None, None, None, None,
                              None, None, None, None, None)

    @property
    def relation(self):
        return self._relation

    def __init__(self, user_rec_ribbon, user_franchise_ribbon, user_recspace_info, update_user_settings, protect_recordings,
                 create_recording, mark_watched, delete_recordings, delete_rules, create_rules, list_rules, bind_rec,
                 update_rules, nothing,
                 redudnant_ts, basic_networ, network_byte_size, small_db, large_db, nginx_check, playback, top_n_playback,
                 get_asset_json, get_asset_jpeg, load_asset, get_airing, load_airing):

        RecAPIRoutesRelation.__init__(self, user_rec_ribbon, user_franchise_ribbon, user_recspace_info, update_user_settings, create_recording,
                                      protect_recordings, mark_watched, delete_recordings, create_rules, delete_rules, list_rules, bind_rec, update_rules,
                                      nothing, redudnant_ts, basic_networ, network_byte_size, small_db, large_db, nginx_check)

        PlaybackRoutesRelation.__init__(self, playback, top_n_playback)

        MetaDataRelation.__init__(self, get_asset_json, get_asset_jpeg, load_asset, get_airing, load_airing)
        playback_and_recapi = merge_dicts(self._playback_relation, self._recapi_relation)
        self._relation = merge_dicts(playback_and_recapi, self._metadata_relation)
