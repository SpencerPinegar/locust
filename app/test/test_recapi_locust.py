from app.Utils.locust_test import LocustTest
from app.Utils.route_relations import RecAPIRoutesRelation

class TestAPILocustUndistributed(LocustTest):

   # def test_misc_route(self):
   #     self._test_undistributed_api()

    def test_user_recordings_ribbon(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.USER_RECORDING_RIBBON, False)

    def test_user_franchise_ribbon(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.USER_FRANCHISE_RIBBON, False)

    def test_user_recspace_information(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.USER_RECSPACE_INFO, False)

    def test_update_user_settings(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.UPDATE_USER_SETTINGS, False)

    # TODO: Update tests to include Create/Delete Recordings and user rules

    def test_protect_recordings(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.PROTECT_RECORDINGS, False)

    def test_mark_watched(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.MARK_WATCHED, False)

    def test_update_rules(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.UPDATE_RULES, False)

    def test_bind_recording_route(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.BIND_RECORDING, False)

    def test_list_rules(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.LIST_RULES, False)

    def test_do_nothing_cpu_used(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.NOTHING, False, False, assert_results=False)

    # def test_redundant_ts_segment(self):
    #     self._test_undistributed_api("Redundant Ts Segment", False)

    def test_basic_network(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.BASIC_NETWORK, False)

    def test_network_byte_size(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.NETWORK_BYTE_SIZE, False)

    def test_small_db(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.SMALL_DB, False)

    def test_large_db(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.LARGE_DB, False)

    def test_nginx_check(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.NGINX_CHECK, False)

class TestAPILocustUndistributedDebug(LocustTest):

    def setUp(self):
        super(TestAPILocustUndistributedDebug, self).setUp()
        self.load_runner.debug = True

   # def test_misc_route(self):
   #     self._test_undistributed_api()

    def test_user_recordings_ribbon(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.USER_RECORDING_RIBBON, False)

    def test_user_franchise_ribbon(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.USER_FRANCHISE_RIBBON, False)

    def test_user_recspace_information(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.USER_RECSPACE_INFO, False)

    def test_update_user_settings(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.UPDATE_USER_SETTINGS, False)

    # TODO: Update tests to include Create/Delete Recordings and user rules

    def test_protect_recordings(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.PROTECT_RECORDINGS, False)

    def test_mark_watched(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.MARK_WATCHED, False)

    def test_update_rules(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.UPDATE_RULES, False)

    def test_bind_recording_route(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.BIND_RECORDING, False)

    def test_list_rules(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.LIST_RULES, False)

    def test_do_nothing_cpu_used(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.NOTHING, False, False, assert_results=False)

    # def test_redundant_ts_segment(self):
    #     self._test_undistributed_api("Redundant Ts Segment", False)

    def test_basic_network(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.BASIC_NETWORK, False)

    def test_network_byte_size(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.NETWORK_BYTE_SIZE, False)

    def test_small_db(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.SMALL_DB, False)

    def test_large_db(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.LARGE_DB, False)

    def test_nginx_check(self):
        self._test_undistributed_recapi(RecAPIRoutesRelation.NGINX_CHECK, False)

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
        self._test_multi_core_undistributed_recapi_custom(custom_api_route, False)

    def test_user_recordings_ribbon(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.USER_RECORDING_RIBBON, False, version=4)

    def test_user_franchise_ribbon(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.USER_FRANCHISE_RIBBON, False)

    def test_user_recspace_information(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.USER_RECSPACE_INFO, False)

    def test_update_user_settings(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.UPDATE_USER_SETTINGS, False)

    # TODO: Update tests to include Create/Delete Recordings and user rules

    def test_protect_recordings(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.PROTECT_RECORDINGS, False)

    def test_mark_watched(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.MARK_WATCHED, False)

    def test_update_rules(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.UPDATE_RULES, False)

    def test_bind_recording_route(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.BIND_RECORDING, False)

    def test_list_rules(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.LIST_RULES, False)

    def test_do_nothing_cpu_used(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.NOTHING, False, False, assert_results=False)

    # def test_redundant_ts_segment(self):
    #     self._test_undistributed_api("Redundant Ts Segment", False)

    def test_basic_network(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.BASIC_NETWORK, False)

    def test_network_byte_size(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.NETWORK_BYTE_SIZE, False)

    def test_small_db(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.SMALL_DB, False)

    def test_large_db(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.LARGE_DB, False)

    def test_nginx_check(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.NGINX_CHECK, False)


class TestAPILocustMultiCoreUndistributedDebug(LocustTest):

    def setUp(self):
        super(TestAPILocustMultiCoreUndistributedDebug, self).setUp()
        self.load_runner.debug = True

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
        self._test_multi_core_undistributed_recapi_custom(custom_api_route, False)

    def test_user_recordings_ribbon(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.USER_RECORDING_RIBBON, False, version=4)

    def test_user_franchise_ribbon(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.USER_FRANCHISE_RIBBON, False)

    def test_user_recspace_information(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.USER_RECSPACE_INFO, False)

    def test_update_user_settings(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.UPDATE_USER_SETTINGS, False)

    # TODO: Update tests to include Create/Delete Recordings and user rules

    def test_protect_recordings(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.PROTECT_RECORDINGS, False)

    def test_mark_watched(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.MARK_WATCHED, False)

    def test_update_rules(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.UPDATE_RULES, False)

    def test_bind_recording_route(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.BIND_RECORDING, False)

    def test_list_rules(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.LIST_RULES, False)

    def test_do_nothing_cpu_used(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.NOTHING, False, False, assert_results=False)

    # def test_redundant_ts_segment(self):
    #     self._test_undistributed_api("Redundant Ts Segment", False)

    def test_basic_network(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.BASIC_NETWORK, False)

    def test_network_byte_size(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.NETWORK_BYTE_SIZE, False)

    def test_small_db(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.SMALL_DB, False)

    def test_large_db(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.LARGE_DB, False)

    def test_nginx_check(self):
        self._test_multi_core_undistributed_recapi(RecAPIRoutesRelation.NGINX_CHECK, False)


class TestAPILocustMultiCoreDistributedDebug(LocustTest):

    def setUp(self):
        super(TestAPILocustMultiCoreDistributedDebug, self).setUp()
        self.load_runner.debug = True

    def test_user_recordings_ribbon(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.USER_RECORDING_RIBBON, False)

    def test_user_franchise_ribbon(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.USER_FRANCHISE_RIBBON, False)

    def test_user_recspace_information(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.USER_RECSPACE_INFO, False)

    def test_update_user_settings(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.UPDATE_USER_SETTINGS, False)

    # TODO: Update tests to include Create/Delete Recordings and user rules

    def test_protect_recordings(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.PROTECT_RECORDINGS, False)

    def test_mark_watched(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.MARK_WATCHED, False)

    def test_update_rules(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.UPDATE_RULES, False)

    def test_list_rules(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.LIST_RULES, False)

    def test_do_nothing_cpu_used(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.NOTHING, False, False, assert_results=False)

    # def test_redundant_ts_segment(self):
    #     self._test_undistributed_api("Redundant Ts Segment", False)

    def test_basic_network(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.BASIC_NETWORK, False)

    def test_network_byte_size(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.NETWORK_BYTE_SIZE, False)

    def test_small_db(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.SMALL_DB, False)

    def test_large_db(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.LARGE_DB, False)

    def test_nginx_check(self):
        self._test_multi_core_distributed_recapi(RecAPIRoutesRelation.NGINX_CHECK, False)
