from app.Utils.locust_test import LocustTest
from app.Utils.route_relations import APIRoutesRelation


class TestAPILocustUndistributed(LocustTest):

    def test_misc_route(self):
        self._test_undistributed_api()

    def test_user_recordings_ribbon(self):
        self._test_undistributed_api(APIRoutesRelation.USER_RECORDING_RIBBON, False)

    def test_user_franchise_ribbon(self):
        self._test_undistributed_api(APIRoutesRelation.USER_FRANCHISE_RIBBON, False)

    def test_user_recspace_information(self):
        self._test_undistributed_api(APIRoutesRelation.USER_RECSPACE_INFO, False)

    def test_update_user_settings(self):
        self._test_undistributed_api(APIRoutesRelation.UPDATE_USER_SETTINGS, False)

    # TODO: Update tests to include Create/Delete Recordings and user rules

    def test_protect_recordings(self):
        self._test_undistributed_api(APIRoutesRelation.PROTECT_RECORDINGS, False)

    def test_mark_watched(self):
        self._test_undistributed_api(APIRoutesRelation.MARK_WATCHED, False)

    def test_update_rules(self):
        self._test_undistributed_api(APIRoutesRelation.UPDATE_RULES, False)

    def test_bind_recording_route(self):
        self._test_undistributed_api(APIRoutesRelation.BIND_RECORDING, False)

    def test_list_rules(self):
        self._test_undistributed_api(APIRoutesRelation.LIST_RULES, False)

    def test_do_nothing_cpu_used(self):
        self._test_undistributed_api(APIRoutesRelation.NOTHING, False, False, assert_results=False)

    # def test_redundant_ts_segment(self):
    #     self._test_undistributed_api("Redundant Ts Segment", False)

    def test_basic_network(self):
        self._test_undistributed_api(APIRoutesRelation.BASIC_NETWORK, False)

    def test_network_byte_size(self):
        self._test_undistributed_api(APIRoutesRelation.NETWORK_BYTE_SIZE, False)

    def test_small_db(self):
        self._test_undistributed_api(APIRoutesRelation.SMALL_DB, False)

    def test_large_db(self):
        self._test_undistributed_api(APIRoutesRelation.LARGE_DB, False)

    def test_nginx_check(self):
        self._test_undistributed_api(APIRoutesRelation.NGINX_CHECK, False)


class TestAPILocustMultiCoreUndistributed(LocustTest):

    def test_api_custom(self):
        custom_api_route = {
            'User Recordings Ribbon': {
                    1: {
                        'norm_lower': 1,
                        'optional_fields': {},
                        'norm_upper': 5,
                        'weight': 15,
                        'size': 4832
                    },
                    2: {
                        'norm_lower': 1,
                        'optional_fields': {},
                        'norm_upper': 5,
                        'weight': 15,
                        'size': 4832
                    },
                    4: {
                        'norm_lower': 1,
                        'optional_fields': {},
                        'norm_upper': 5,
                        'weight': 15,
                        'size': 4832
                    },
                    5: {
                        'norm_lower': 1,
                        'optional_fields': {},
                        'norm_upper': 5,
                        'weight': 15,
                        'size': 4832
                    }
                }
        }
        self._test_multi_core_undistributed_api_custom(custom_api_route, False)

    def test_user_recordings_ribbon(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.USER_RECORDING_RIBBON, False, version=4)

    def test_user_franchise_ribbon(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.USER_FRANCHISE_RIBBON, False)

    def test_user_recspace_information(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.USER_RECSPACE_INFO, False)

    def test_update_user_settings(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.UPDATE_USER_SETTINGS, False)

    # TODO: Update tests to include Create/Delete Recordings and user rules

    def test_protect_recordings(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.PROTECT_RECORDINGS, False)

    def test_mark_watched(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.MARK_WATCHED, False)

    def test_update_rules(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.UPDATE_RULES, False)

    def test_bind_recording_route(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.BIND_RECORDING, False)

    def test_list_rules(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.LIST_RULES, False)

    def test_do_nothing_cpu_used(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.NOTHING, False, False, assert_results=False)

    # def test_redundant_ts_segment(self):
    #     self._test_undistributed_api("Redundant Ts Segment", False)

    def test_basic_network(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.BASIC_NETWORK, False)

    def test_network_byte_size(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.NETWORK_BYTE_SIZE, False)

    def test_small_db(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.SMALL_DB, False)

    def test_large_db(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.LARGE_DB, False)

    def test_nginx_check(self):
        self._test_multi_core_undistributed_api(APIRoutesRelation.NGINX_CHECK, False)


class TestAPILocustMultiCoreDistributed(LocustTest):

    def test_user_recordings_ribbon(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.USER_RECORDING_RIBBON, False)

    def test_user_franchise_ribbon(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.USER_FRANCHISE_RIBBON, False)

    def test_user_recspace_information(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.USER_RECSPACE_INFO, False)

    def test_update_user_settings(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.UPDATE_USER_SETTINGS, False)

    # TODO: Update tests to include Create/Delete Recordings and user rules

    def test_protect_recordings(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.PROTECT_RECORDINGS, False)

    def test_mark_watched(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.MARK_WATCHED, False)

    def test_update_rules(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.UPDATE_RULES, False)

    def test_list_rules(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.LIST_RULES, False)

    def test_do_nothing_cpu_used(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.NOTHING, False, False, assert_results=False)

    # def test_redundant_ts_segment(self):
    #     self._test_undistributed_api("Redundant Ts Segment", False)

    def test_basic_network(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.BASIC_NETWORK, False)

    def test_network_byte_size(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.NETWORK_BYTE_SIZE, False)

    def test_small_db(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.SMALL_DB, False)

    def test_large_db(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.LARGE_DB, False)

    def test_nginx_check(self):
        self._test_multi_core_distributed_api(APIRoutesRelation.NGINX_CHECK, False)
