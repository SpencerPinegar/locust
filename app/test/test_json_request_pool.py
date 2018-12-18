from app.Utils.locust_test import LocustTest, RequestPoolFactory
import hashlib
import json
import requests
import random
import math
from app.Utils.utils import execute_select_statement, get_api_info
from app.Utils.route_relations import (RecAPIRoutesRelation as APIRelation, PlaybackRoutesRelation as PlaybackRelation,
                                       MetaDataRelation as MetaRelation)

RS_Recordings_Key = "rs_recordings"
Seasons_Key = "seasons"
Franchise_Rules_Key = "franchise_rules"


class TestRequestPool(LocustTest):
    # These are just distribution variables
    Max_Processes = 15
    Max_Machines = 4



    def assert_all_subsets_divide_correctly(self, route, is_api=True, *args):
        full_pool = self._get_full_pool(route, *args)
        if isinstance(full_pool, dict):
            the_size = len(full_pool.values()[0].pool)
        else:
            assert isinstance(full_pool, list)
            the_size = len(full_pool)
        max_mach = int(max(min(TestRequestPool.Max_Machines, math.floor(the_size/15)), 1))
        max_proc = int(max(min(TestRequestPool.Max_Processes, math.floor(the_size/max_mach)), 1))
        print("Max Processes Count: {p}   --    Max Machines Count {m}   --   Data Size : {d}".format(
            p=max_proc, m=max_mach, d=the_size
        ))
        for machine_count in range(1, max_mach + 1):
            for process_count in range(1, max_proc + 1, 3):
                divided_pools = self.__get_subdivided_pool(process_count, machine_count, route, *args)
                self.__assert_divided_correctly(full_pool, divided_pools, is_api)

    def __assert_divided_correctly(self, full_list, list_of_subsets, is_api):
        if is_api:
            for version in full_list.keys():
                # Go to the specific version
                subsets_params = [subset[version] for subset in list_of_subsets]
                full_params = full_list[version]
                # Get the route set to compare the endpoints
                subsets_route = set([subset.route for subset in subsets_params])
                full_route = set([full_params.route])
                # Get the normal pools for comparison
                subset_normal_pools = [subset.pool.normal_pool for subset in subsets_params]
                bonded_normal_pools = []
                for subset_pool in subset_normal_pools:
                    bonded_normal_pools += subset_pool
                full_pool = full_params.pool.normal_pool
                # Run the actual checks
                self.assertSetEqual(subsets_route, full_route,
                                    "The routes where not the same for all subsection of the pool")
                self.assertListEqual(sorted(bonded_normal_pools), sorted(full_pool),
                                     "The data was not distributed correctly")
        else:
            # See if the subsets equal the full set
            full_pool = full_list
            bonded_normal_pools = []
            for subset in list_of_subsets:
                bonded_normal_pools += subset
            self.assertListEqual(sorted(bonded_normal_pools), sorted(full_pool),
                                 "The data was not distributed correctly")

    def __get_subdivided_pool(self, processes_per_machine, num_machines, route, *args):
        max_route_length = self.load_runner._get_pool_length(route, self.env, *args)
        subdivided_pools = []
        ranges = []
        for machine_index in range(num_machines):
            for process_index in range(processes_per_machine):
                self._reset_request_pool_factory(process_index, processes_per_machine-1, machine_index,
                                                 num_machines-1, max_route_length)
                range_n_offset = self.PoolFactory._get_start_offset_and_size()
                ranges.append(range_n_offset)
                to_be_added = self.PoolFactory.get_route_pool_and_ribbon(route,*args)
                subdivided_pools.append(to_be_added)
        print("           ")
        print("       ")
        print("Processes Count: {p}   --   Machines Count: {m}".format(p=processes_per_machine, m=num_machines))

        for item in ranges:
            print("Offset: {o}   --   Size: {s}".format(o=item.offset, s=item.size))
        ac_size = sum([x.size for x in ranges])
        print("Expected Size: {e}   --  Actual Size: {a}".format(e=max_route_length, a=ac_size))
        return subdivided_pools

    def _get_full_pool(self, route, *args):
        self._reset_request_pool_factory(0, 0, 0, 0, None)
        return self.PoolFactory.get_route_pool_and_ribbon(route, *args)

    def _assert_size_n_offset(self, expected_size, expected_offset):
        size_n_offest = self.PoolFactory._get_start_offset_and_size()
        self.assertEqual(size_n_offest.size, expected_size, "The Request Pool Wanted Size should be {}".format(expected_size))
        self.assertEqual(size_n_offest.offset, expected_offset, "The Request Pool Wanted offset should be {}".format(expected_offset))

    def _reset_request_pool_factory(self, slave_int, max_slave_int, comp_int, max_comp_int, max_size):
        self.PoolFactory = RequestPoolFactory(self.config, comp_int, max_comp_int, slave_int, max_slave_int, max_size, [self.env])


class TestReadOnlyRequestPool(TestRequestPool):
    # Easy access to error messages
    Non_Inited_Data_Pool_Mssg = "The DataPool failed when trying to create normal JSON data -- Check the datapool initlization code"
    Non_200_Post_Mssg = "The JSON Post request was not properly proccessed by the server -- see the relevant network error code"
    Non_Normal_Length_Mssg = "The JSON data size does not reflect a normal user -- see the relevant SQL statement and the Normal Min/Max data in the SETTINGS.yaml file"
    # API Info listed here so it is available to all methods
    USER_RECORDINGS_RIBBON_API_INFO = {
        1: {
            "size": 30,
            "norm_lower": 20,
            "norm_upper": 50,
            "optional_fields": {},
            "weight": 1
        },
        2: {
            "size": 30,
            "norm_lower": 20,
            "norm_upper": 50,
            "optional_fields": {},
            "weight": 4
        },
        4: {
            "size": 30,
            "norm_lower": 20,
            "norm_upper": 50,
            "optional_fields": {},
            "weight": 2
        }
    }
    USER_FRANCHISE_RIBBON_API_INFO = {
        1: {
            "size": 30,
            "norm_lower": 40,
            "norm_upper": 50,
            "optional_fields": {},
            "weight": 1
        },
        4: {
            "size": 30,
            "norm_lower": 40,
            "norm_upper": 50,
            "optional_fields": {},
            "weight": 2
        }
    }
    USER_RECSPACE_INFO_API_INFO = {
        1: {
            "size": 30,
            "norm_lower": 40,
            "norm_upper": 50,
            "optional_fields": {},
            "weight": 5
        }
    }
    MARK_WATCHED_API_INFO = {
        1: {
            "size": 30,
            "norm_lower": 40,
            "norm_upper": 50,
            "optional_fields": {},
            "weight": 2
        }
    }
    LIST_RULES_API_INFO = {
        1: {
            "size": 30,
            "norm_lower": 2,
            "norm_upper": 7,
            "optional_fields": {},
            "weight": 1
        },
        4: {
            "size": 30,
            "norm_lower": 2,
            "norm_upper": 7,
            "optional_fields": {},
            "weight": 4
        }
    }
    GET_ASSET_JSON_API_INFO = {
        1: {
            "size": 100,
            "norm_lower": 1,
            "norm_upper": 1,
            "optional_fields": {},
            "weight": 1
        }
    }
    GET_ASSET_JPEG_API_INFO = {
        1: {
            "size": 100,
            "norm_lower": 1,
            "norm_upper": 1,
            "optional_fields": {},
            "weight": 1
        }
    }
    LOAD_ASSET_API_INFO = {
        1: {
            "size": 100,
            "norm_lower": 1,
            "norm_upper": 20,
            "optional_fields": {},
            "weight": 1
        }
    }


    def test_size_property(self):
        self._reset_request_pool_factory(0, 0, 0, 0, 30)
        self.assertEqual(self.PoolFactory.size, 30, "The size property's get function doesn't work")
        self.PoolFactory.size = 3
        self.assertEqual(self.PoolFactory.size, 3, "The size property's set function doesn't work")

    def test_chunk(self):
        self._reset_request_pool_factory(0, 0, 0, 0, None)
        self.assertFalse(self.PoolFactory.chunk, "The pool factory should tell data pools to chunk if size is specified")
        self._reset_request_pool_factory(0, 0, 0, 0, 300)
        self.assertTrue(self.PoolFactory.chunk, "The pool factory should tell data pools to chunk if size is specified")

    def test_get_start_offset_and_size_single_process_single_machine(self):
        # check a basic non_chunked size n offset (most basic case)
        self._reset_request_pool_factory(0, 0, 0, 0, None)
        self._assert_size_n_offset(None, 0)
        # check a basic non_chunked size n offset (second most basic case)
        self._reset_request_pool_factory(0, 0, 0, 0, 100)
        self._assert_size_n_offset(100, 0)

    def test_get_start_offset_and_size_multi_process_single_machine(self):
        # check a basic even multi process even size - process 1
        self._reset_request_pool_factory(0, 1, 0, 0, 100)
        self._assert_size_n_offset(50, 0)
        # continue even process even size - process 2
        self._reset_request_pool_factory(1, 1, 0, 0, 100)
        self._assert_size_n_offset(50, 50)

        # check a basic odd multi process size even - process 1
        self._reset_request_pool_factory(0, 2, 0, 0, 100)
        self._assert_size_n_offset(33, 0)
        # continue odd process even size - process 2
        self._reset_request_pool_factory(1, 2, 0, 0, 100)
        self._assert_size_n_offset(33, 33)
        # continue odd process even size - process 3
        self._reset_request_pool_factory(2, 2, 0, 0, 100)
        self._assert_size_n_offset(34, 66)

        # check a basic even multi process odd size - process 1
        self._reset_request_pool_factory(0, 1, 0, 0, 101)
        self._assert_size_n_offset(50, 0)
        # continue even process odd size - process 2
        self._reset_request_pool_factory(1, 1, 0, 0, 101)
        self._assert_size_n_offset(51, 50)

        # check a basic odd multi process odd size - process 1
        self._reset_request_pool_factory(0, 2, 0, 0, 101)
        self._assert_size_n_offset(33, 0)
        # continue odd process odd size - process 2
        self._reset_request_pool_factory(1, 2, 0, 0, 101)
        self._assert_size_n_offset(33, 33)
        # continue odd process odd size - process 3
        self._reset_request_pool_factory(2, 2, 0, 0, 101)
        self._assert_size_n_offset(35, 66)

    def test_get_start_offset_and_size_multi_process_multi_machine(self):
        ##################### EVEN EVEN EVEN ########################
        # check a basic even multi machine even multi process even size - machine 1, process 1
        self._reset_request_pool_factory(0, 1, 0, 1, 100)
        self._assert_size_n_offset(25, 0)
        # continue even machine, even process, even size - machine 1, process 2
        self._reset_request_pool_factory(1, 1, 0, 1, 100)
        self._assert_size_n_offset(25, 25)
        # continue even machine, even process, even size - machine 2, process 1
        self._reset_request_pool_factory(0, 1, 1, 1, 100)
        self._assert_size_n_offset(25, 50)
        # continue even machine, even process, even size - machine 2, process 2
        self._reset_request_pool_factory(1, 1, 1, 1, 100)
        self._assert_size_n_offset(25, 75)

        #################### EVEN EVEN ODD ##########################
        # check a basic even multi machine even multi process odd size - machine 1, process 1
        self._reset_request_pool_factory(0, 1, 0, 1, 101)
        self._assert_size_n_offset(25, 0)
        # continue even machine, even process, odd size - machine 1, process 2
        self._reset_request_pool_factory(1, 1, 0, 1, 101)
        self._assert_size_n_offset(25, 25)
        # continue even machine, even process, odd size - machine 2, process 1
        self._reset_request_pool_factory(0, 1, 1, 1, 101)
        self._assert_size_n_offset(25, 50)
        # continue even machine, even process, odd size - machine 2, process 2
        self._reset_request_pool_factory(1, 1, 1, 1, 101)
        self._assert_size_n_offset(26, 75)

        ##################### EVEN ODD EVEN ########################
        # check a basic even multi machine, odd multi process even size - machine 1, process 1
        self._reset_request_pool_factory(0, 2, 0, 1, 100)
        self._assert_size_n_offset(16, 0)
        # continue even machine, odd process, even size - machine 1, process 2
        self._reset_request_pool_factory(1, 2, 0, 1, 100)
        self._assert_size_n_offset(16, 16)
        # continue even machine, odd process, even size - machine 1, process 3
        self._reset_request_pool_factory(2, 2, 0, 1, 100)
        self._assert_size_n_offset(18, 32)
        # continue even machine, odd process, even size - machine 2, process 1
        self._reset_request_pool_factory(0, 2, 1, 1, 100)
        self._assert_size_n_offset(16, 50)
        # continue even machine, odd process, even size - machine 2, process 2
        self._reset_request_pool_factory(1, 2, 1, 1, 100)
        self._assert_size_n_offset(16, 66)
        # continue even machine, odd process, even size - machine 2, process 3
        self._reset_request_pool_factory(2, 2, 1, 1, 100)
        self._assert_size_n_offset(18, 82)

        ##################### EVEN ODD ODD ########################
        # check a basic even multi machine, odd multi process odd size - machine 1, process 1
        self._reset_request_pool_factory(0, 2, 0, 1, 101)
        self._assert_size_n_offset(16, 0)
        # continue even machine, odd process, odd size - machine 1, process 2
        self._reset_request_pool_factory(1, 2, 0, 1, 101)
        self._assert_size_n_offset(16, 16)
        # continue even machine, odd process, odd size - machine 1, process 3
        self._reset_request_pool_factory(2, 2, 0, 1, 101)
        self._assert_size_n_offset(18, 32)
        # continue even machine, odd process, odd size - machine 2, process 1
        self._reset_request_pool_factory(0, 2, 1, 1, 101)
        self._assert_size_n_offset(17, 50)
        # continue even machine, odd process, odd size - machine 2, process 2
        self._reset_request_pool_factory(1, 2, 1, 1, 101)
        self._assert_size_n_offset(17, 67)
        # continue even machine, odd process, odd size - machine 2, process 3
        self._reset_request_pool_factory(2, 2, 1, 1, 101)
        self._assert_size_n_offset(17, 84)

        #################### ODD EVEN EVEN #############################
        # check a basic odd multi machine even multi process even size - machine 1, process 1
        self._reset_request_pool_factory(0, 1, 0, 2, 100)
        self._assert_size_n_offset(16, 0)
        # continue odd machine, even process, even size - machine 1, process 2
        self._reset_request_pool_factory(1, 1, 0, 2, 100)
        self._assert_size_n_offset(17, 16)
        # continue odd machine, even process, even size - machine 2, process 1
        self._reset_request_pool_factory(0, 1, 1, 2, 100)
        self._assert_size_n_offset(16, 33)
        # continue odd machine, even process, even size - machine 2, process 2
        self._reset_request_pool_factory(1, 1, 1, 2, 100)
        self._assert_size_n_offset(17, 49)
        # continue odd machine, even process, even size - machine 3, process 1
        self._reset_request_pool_factory(0, 1, 2, 2, 100)
        self._assert_size_n_offset(17, 66)
        # continue odd machine, even process, even size - machine 3, process 2
        self._reset_request_pool_factory(1, 1, 2, 2, 100)
        self._assert_size_n_offset(17, 83)

        ################### ODD EVEN ODD #####################################
        # check a basic odd multi machine even multi process odd size - machine 1, process 1
        self._reset_request_pool_factory(0, 1, 0, 2, 101)
        self._assert_size_n_offset(16, 0)
        # continue odd machine, even process, odd size - machine 1, process 2
        self._reset_request_pool_factory(1, 1, 0, 2, 101)
        self._assert_size_n_offset(17, 16)
        # continue odd machine, even process, odd size - machine 2, process 1
        self._reset_request_pool_factory(0, 1, 1, 2, 101)
        self._assert_size_n_offset(16, 33)
        # continue odd machine, even process, odd size - machine 2, process 2
        self._reset_request_pool_factory(1, 1, 1, 2, 101)
        self._assert_size_n_offset(17, 49)
        # continue odd machine, even process, odd size - machine 3, process 1
        self._reset_request_pool_factory(0, 1, 2, 2, 101)
        self._assert_size_n_offset(17, 66)
        # continue odd machine, even process, odd size - machine 3, process 2
        self._reset_request_pool_factory(1, 1, 2, 2, 101)
        self._assert_size_n_offset(18, 83)

        #################### ODD ODD EVEN #############################
        # check a basic odd multi machine, odd multi process, even size - machine 1, process 1
        self._reset_request_pool_factory(0, 2, 0, 2, 100)
        self._assert_size_n_offset(11, 0)
        # continue odd machine, odd process, even size - machine 1, process 2
        self._reset_request_pool_factory(1, 2, 0, 2, 100)
        self._assert_size_n_offset(11, 11)
        # continue odd machine, odd process, even size - machine 1, process 3
        self._reset_request_pool_factory(2, 2, 0, 2, 100)
        self._assert_size_n_offset(11, 22)
        # continue odd machine, odd process, even size - machine 2, process 1
        self._reset_request_pool_factory(0, 2, 1, 2, 100)
        self._assert_size_n_offset(11, 33)
        # continue odd machine, odd process, even size - machine 2, process 2
        self._reset_request_pool_factory(1, 2, 1, 2, 100)
        self._assert_size_n_offset(11, 44)
        # continue odd machine, odd process, even size - machine 2, process 3
        self._reset_request_pool_factory(2, 2, 1, 2, 100)
        self._assert_size_n_offset(11, 55)
        # continue odd machine, odd process, even size - machine 3, process 1
        self._reset_request_pool_factory(0, 2, 2, 2, 100)
        self._assert_size_n_offset(11, 66)
        # continue odd machine, odd process, even size - machine 3, process 2
        self._reset_request_pool_factory(1, 2, 2, 2, 100)
        self._assert_size_n_offset(11, 77)
        # continue odd machine, odd process, even size - machine 3, process 3
        self._reset_request_pool_factory(2, 2, 2, 2, 100)
        self._assert_size_n_offset(12, 88)

        #################### ODD ODD ODD #############################
        # check a basic odd multi machine, odd multi process, odd size - machine 1, process 1
        self._reset_request_pool_factory(0, 2, 0, 2, 101)
        self._assert_size_n_offset(11, 0)
        # continue odd machine, odd process, odd size - machine 1, process 2
        self._reset_request_pool_factory(1, 2, 0, 2, 101)
        self._assert_size_n_offset(11, 11)
        # continue odd machine, odd process, odd size - machine 1, process 3
        self._reset_request_pool_factory(2, 2, 0, 2, 101)
        self._assert_size_n_offset(11, 22)
        # continue odd machine, odd process, odd size - machine 2, process 1
        self._reset_request_pool_factory(0, 2, 1, 2, 101)
        self._assert_size_n_offset(11, 33)
        # continue odd machine, odd process, odd size - machine 2, process 2
        self._reset_request_pool_factory(1, 2, 1, 2, 101)
        self._assert_size_n_offset(11, 44)
        # continue odd machine, odd process, odd size - machine 2, process 3
        self._reset_request_pool_factory(2, 2, 1, 2, 101)
        self._assert_size_n_offset(11, 55)
        # continue odd machine, odd process, odd size - machine 3, process 1
        self._reset_request_pool_factory(0, 2, 2, 2, 101)
        self._assert_size_n_offset(11, 66)
        # continue odd machine, odd process, odd size - machine 3, process 2
        self._reset_request_pool_factory(1, 2, 2, 2, 101)
        self._assert_size_n_offset(11, 77)
        # continue odd machine, odd process, odd size - machine 3, process 3
        self._reset_request_pool_factory(2, 2, 2, 2, 101)
        self._assert_size_n_offset(13, 88)

    def test_process_without_work(self):
        self._reset_request_pool_factory(0, 1, 0, 0, 1)
        self._assert_size_n_offset(0, 0)
        self._reset_request_pool_factory(1, 1, 0, 0, 1)
        self._assert_size_n_offset(1, 0)

    def test_machine_without_work(self):
        self._reset_request_pool_factory(0, 0, 0, 2, 2)
        self._assert_size_n_offset(0, 0)
        self._reset_request_pool_factory(0, 0, 1, 2, 2)
        self._assert_size_n_offset(0, 0)
        self._reset_request_pool_factory(0, 0, 2, 2, 2)
        self._assert_size_n_offset(2, 0)
    def test_user_recordings_ribbon_single_core(self):
        route, api_route = APIRelation.USER_RECORDING_RIBBON, TestReadOnlyRequestPool.USER_RECORDINGS_RIBBON_API_INFO
        version_info = self._get_full_pool(route, api_route, self.env)
        for version, version_params in version_info.items():
            url = self.dev2_recapi_host + version_params.route
            datapool = version_params.pool
            self.assertFalse(datapool.pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
            # Must initlize to be valid
            json_post = datapool.get_json()
            response = requests.post(url, json=json_post)
            self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
            #this test wont be valid unless we have a 200 response
            recordings = json.loads(response.content)[RS_Recordings_Key]
            rec_count = self._recording_count(recordings)
            api_info = get_api_info(TestReadOnlyRequestPool.USER_RECORDINGS_RIBBON_API_INFO[version])
            min_length = api_info.element_lb
            max_length = api_info.element_ub
            self.assertTrue(min_length <= rec_count <= max_length, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)

    def test_user_recordings_ribbon_distributed(self):
        # Get the full pool
        route, api_route = APIRelation.USER_RECORDING_RIBBON, TestReadOnlyRequestPool.USER_RECORDINGS_RIBBON_API_INFO
        self.assert_all_subsets_divide_correctly(route, True, api_route, self.env)

    def test_user_franchise_ribbon_single_core(self):
        route, api_call = APIRelation.USER_FRANCHISE_RIBBON, TestReadOnlyRequestPool.USER_FRANCHISE_RIBBON_API_INFO
        version_info = self.PoolFactory.get_user_franchise_ribbon_pool_and_route(api_call, "DEV2")
        for version, version_params in version_info.items():
            url = self.dev2_recapi_host + version_params.route
            datapool = version_params.pool
            self.assertFalse(datapool.pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
            json_post_post = datapool.get_json(filter="recorded")
            response = requests.post(url, json=json_post_post)
            self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
            # this test wont be valid unless we have a 200 response
            seasons = json.loads(response.content)[Seasons_Key]
            episodes = self._franchise_count(seasons)
            api_info = get_api_info(api_call[version])
            min_length = api_info.element_lb
            max_length = api_info.element_ub
            self.assertTrue(min_length <= episodes <= max_length, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)

    def test_user_franchise_ribbon_distributed(self):
        route, api_call = APIRelation.USER_FRANCHISE_RIBBON, TestReadOnlyRequestPool.USER_FRANCHISE_RIBBON_API_INFO
        self.assert_all_subsets_divide_correctly(route, True, api_call, self.env)

    def test_user_recspace_information_single_core(self):
        route, api_call = APIRelation.USER_RECSPACE_INFO, TestReadOnlyRequestPool.USER_RECSPACE_INFO_API_INFO
        version_info = self.PoolFactory.get_user_recspace_information_pool_and_route(api_call, "DEV2")
        for version, version_params in version_info.items():
            url = self.dev2_recapi_host + version_params.route
            datapool = version_params.pool
            self.assertFalse(datapool.pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
            json_post_post = datapool.get_json()
            response = requests.post(url, json=json_post_post)
            self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
            # this test wont be valid unless we have a 200 response

    def test_user_recspace_information_distributed(self):
        route, api_call = APIRelation.USER_RECSPACE_INFO, TestReadOnlyRequestPool.USER_RECSPACE_INFO_API_INFO
        self.assert_all_subsets_divide_correctly(route, True, api_call, self.env)

    def test_mark_watched_single_core(self):
        route, api_call = APIRelation.MARK_WATCHED, TestReadOnlyRequestPool.MARK_WATCHED_API_INFO
        version_info = self.PoolFactory.get_mark_watched_pool_and_route(api_call, "DEV2")
        for version, version_params in version_info.items():
            url = self.dev2_recapi_host + version_params.route
            datapool = version_params.pool
            self.assertFalse(datapool.pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
            json_post_post = datapool.get_json()
            response = requests.post(url, json=json_post_post)
            self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
            # this test wont be valid unless we have a 200 response

    def test_mark_watched_distributed(self):
        route, api_call = APIRelation.MARK_WATCHED, TestReadOnlyRequestPool.MARK_WATCHED_API_INFO
        self.assert_all_subsets_divide_correctly(route, True, api_call, self.env)

    def test_list_rules_single_core(self):
        route, api_call = APIRelation.LIST_RULES, TestReadOnlyRequestPool.LIST_RULES_API_INFO
        version_info = self.PoolFactory.get_list_rules_pool_and_route(api_call, "DEV2")
        for version, version_params in version_info.items():
            url = self.dev2_recapi_host + version_params.route
            datapool = version_params.pool
            self.assertFalse(datapool.pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)

            json_post_post = datapool.get_json()
            response = requests.post(url, json=json_post_post)
            self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
            amount_of_rules = len(json.loads(response.content)[Franchise_Rules_Key])
            api_info = get_api_info(api_call[version])
            min_rules = api_info.element_lb
            max_rules = api_info.element_ub
            self.assertTrue(min_rules <= amount_of_rules <= max_rules, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)

    def test_list_rules_distributed(self):
        route, api_call = APIRelation.LIST_RULES, TestReadOnlyRequestPool.LIST_RULES_API_INFO
        self.assert_all_subsets_divide_correctly(route, True, api_call, self.env)


    def test_get_load_asset(self):
        route, api_call = MetaRelation.LOAD_ASSET, TestReadOnlyRequestPool.LOAD_ASSET_API_INFO
        version_info = self.PoolFactory.get_load_asset(api_call, "DEV2")
        for version, version_params in version_info.items():
            url = self.dev2_metadata_host + version_params.route
            datapool = version_params.pool
            json_post_post = random.choice(datapool)
            self.assertFalse(len(datapool) is -1,TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
            response = requests.put(url, json=json_post_post)
            self.assertEqual(202, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)






    def _recording_count(self, recordings):
        rec_count = 0
        for rec in recordings:
            try:
                rec_count += int(rec["num_episodes"])
            except KeyError as e:
                rec_count += 1
        return rec_count

    def _franchise_count(self, franchise_seasons):
        resp_len = 0
        for season in franchise_seasons:
            resp_len += len(season["episodes"])
        return resp_len




class TestTwoStateRequestPool(TestRequestPool):

    UPDATE_USER_SETTINGS_API_INFO = {
            1: {
                "size": 30,
                "norm_lower": 40,
                "norm_upper": 50,
                "optional_fields": {},
                "weight": 1
            }
        }
    UPDATE_RULES_API_INFO = {
            1: {
                "size": 30,
                "norm_lower": 40,
                "norm_upper": 50,
                "optional_fields": {},
                "weight": 3
            }
        }

    def test_update_user_settings_single_core(self):
        route_name, api_call, user_desc, env, clean_default, dirty_default = (APIRelation.UPDATE_USER_SETTINGS,
                                                                              TestTwoStateRequestPool.UPDATE_USER_SETTINGS_API_INFO,
                                                                    "update_user_settings", self.env, 599, 80085)
        user_count = max([x["size"] for x in api_call.values()])
        current_user_count = self.data_factory.users_count(env, user_desc)
        if current_user_count < user_count:
            self.data_factory.create_users(env, user_desc, user_count - current_user_count)
        elif current_user_count > user_count:
            self.data_factory.delete_users(env, user_desc, user_count)
        post_user_count = self.data_factory.users_count(env, user_desc)
        self.assertEqual(post_user_count, user_count, "Your users where not created correctly")
        abs_size = len(execute_select_statement(self.config, route_name, env))
        self.assertGreaterEqual(abs_size, post_user_count, "You could not find all users with desc {}".format(user_desc))
        version_info = self.PoolFactory.get_update_user_settngs_pool_and_route(api_call, env)
        for version, version_params in version_info.items():
            pool = version_params.pool
            route = version_params.route
            route = self.config.recapi.get_host(env) + route
            api_info = get_api_info(api_call[version])
            self.assertEqual(api_info.size, len(pool), "The pool created was not the correct size")
            pool.close(route)
            clean_state = execute_select_statement(self.config, route_name, env)
            for user in clean_state:
                self.assertEqual(user[1], clean_default)
            pool.flip_state()
            self.assertTrue(pool.current_default_params, pool.start_state_params)
            self.assertEqual(0, pool.index)
            for request in range(abs_size):  # range based off number of relevant users
                json = pool.get_json()
                response = requests.post(route, json=json)
                self.assertEqual(response.status_code, 200)
            dirty_state = execute_select_statement(self.config, route_name, env)
            self.assertEqual(len(dirty_state), abs_size)
            for user in dirty_state:
                self.assertEqual(user[1], dirty_default)
            for reqeust in range(abs_size):
                json = pool.get_json()
                response = requests.post(route, json=json)
                self.assertTrue(response.status_code is 200)
            reclean_state = execute_select_statement(self.config, route_name, env)
            for user in reclean_state:
                self.assertEqual(user[1], clean_default)
            pool.close(route)



    #There are 400 recordings that we can pull from to mark as protected or not
    # def test_protect_recordings_v1(self):
    #
    #     route_name, version, env, clean_default, dirty_default = ("Protect Recordings", 1, "DEV2",  True, False)
    #     abs_size = len(execute_select_statement(self.config, route_name, env))
    #     self.assertGreater(abs_size, 100)
    #     pool, route = self.PoolFactory.get_protect_recordings_pool_and_route(version, env, abs_size, abs_size)
    #     url = self.dev2_host + route
    #     self.assertEqual(len(pool.normal_pool), abs_size)
    #     pool.close(url)
    #     clean_state = execute_select_statement(self.config, route_name, env)
    #     self.assertEqual(len(clean_state), abs_size) #We should have grabbed all 400 recordings
    #     for recording in clean_state:
    #         self.assertEqual(recording[1], clean_default)
    #     pool.flip_state()
    #     self.assertTrue(pool.current_default_params, pool.start_state_params)
    #     self.assertEqual(0, pool.index)
    #     for request in range(abs_size): # range based off number of relevant recordings
    #         json = pool.get_json()
    #         response = requests.post(url, json=json)
    #         self.assertEqual(response.status_code, 200)
    #     dirty_state = execute_select_statement(self.config, route_name, env)
    #     self.assertEqual(len(dirty_state), abs_size)
    #     for recording in dirty_state:
    #         self.assertEqual(recording[1], dirty_default)
    #     for reqeust in range(abs_size):
    #         json = pool.get_json()
    #         response = requests.post(url, json=json)
    #         self.assertTrue(response.status_code is 200)
    #     reclean_state = execute_select_statement(self.config, route_name, env)
    #     for recording in reclean_state:
    #         self.assertEqual(recording[1], clean_default)
    #     pool.close(url)

    def test_update_rules_single_core(self):

        route_name, api_call, user_desc, version, env, clean_default, dirty_default = (APIRelation.UPDATE_RULES,
                                                                                       TestTwoStateRequestPool.UPDATE_RULES_API_INFO,
                                                                                       "update_user_rules", 1, "DEV2", 2, 1)
        user_count = max([get_api_info(x).size for x in api_call.values()])
        current_user_count = self.data_factory.users_count(env, user_desc)
        #set and verify number of users
        if current_user_count < user_count:
            self.data_factory.create_users(env, user_desc, user_count - current_user_count)
        elif current_user_count > user_count:
            self.data_factory.delete_rules(env, user_desc, 0)
            self.data_factory.delete_users(env, user_desc, user_count)
        post_user_count = self.data_factory.users_count(env, user_desc)
        self.assertEqual(post_user_count, user_count, "Your users where not created correctly")
        if self.data_factory.rules_exist(1, 1, env, user_desc):
            self.data_factory.create_rules(env, user_desc, 1)
            self.data_factory.delete_rules(env, user_desc, 1)
        abs_size = len(execute_select_statement(self.config, route_name, env))
        self.assertGreaterEqual(abs_size, post_user_count,
                                "You could not find all users with desc {}".format(user_desc))

        self.assertTrue(self.data_factory.rules_exist(1, 1, env, user_desc), "user rules where not created correctly")
        version_info = self.PoolFactory.get_update_rules_pool_and_route(api_call, env)
        for version, version_params in version_info.items():
            pool = version_params.pool
            route = version_params.route
            route = self.config.recapi.get_host(env) + route
            api_info = get_api_info(api_call[version])
            self.assertEqual(api_info.size, len(pool), "The pool created was not the correct size")
            pool.close(route)
            clean_state = execute_select_statement(self.config, route_name, env)
            for user in clean_state:
                self.assertEqual(user[0], clean_default)
            pool.flip_state()
            self.assertTrue(pool.current_default_params, pool.start_state_params)
            self.assertEqual(0, pool.index)
            for request in range(abs_size):  # range based off number of relevant users
                json = pool.get_json()
                response = requests.post(route, json=json)
                self.assertEqual(response.status_code, 200)
            dirty_state = execute_select_statement(self.config, route_name, env)
            self.assertEqual(len(dirty_state), abs_size)
            for user in dirty_state:
                self.assertEqual(user[0], dirty_default)
            for reqeust in range(abs_size):
                json = pool.get_json()
                response = requests.post(route, json=json)
                self.assertTrue(response.status_code is 200)
            reclean_state = execute_select_statement(self.config, route_name, env)
            for user in reclean_state:
                self.assertEqual(user[0], clean_default)
            pool.close(route)

    def test_update_rules_distributed(self):
        route_name, api_info = APIRelation.UPDATE_RULES, TestTwoStateRequestPool.UPDATE_RULES_API_INFO
        self.assert_all_subsets_divide_correctly(route_name, True, api_info, self.env)


    def test_update_user_settings_distributed(self):
        route_name, api_call = APIRelation.UPDATE_USER_SETTINGS, TestTwoStateRequestPool.UPDATE_USER_SETTINGS_API_INFO
        self.assert_all_subsets_divide_correctly(route_name, True, api_call, self.env)



class TestMiscFunctions(TestRequestPool):


    def test_get_playback_recording_single_core(self):
        route_name, version = (PlaybackRelation.Playback, None)
        dvr, size = 1124, 50

        recordings = self.PoolFactory.get_recent_playback_recording(dvr, 10, size)
        self.assertEqual(size, len(recordings), "The amount of recordings received was not the amount asked for")
        for asset_info in recordings:
            self.assertTrue(str(dvr) in asset_info.url, "The QMX was not from the dvr you requested")

    def test_get_playback_recording_distributed(self):
        route_name, api_info = PlaybackRelation.Playback, None
        dvr, days_old, count = 1109, 60, 600
        self.assert_all_subsets_divide_correctly(route_name, False, dvr, days_old, count)

    def test_get_top_n_recording_single_core(self):
        route_name, version = PlaybackRelation.Top_N_Playback, None
        recordings = self.PoolFactory.get_top_n_channels_in_last_day()
        self.assertGreater(len(recordings), 20, "There where less than 20 episodes recorded on the top N channels for the last day?")

    def test_get_top_n_recording_distributed(self):
        route_name, api_info = PlaybackRelation.Top_N_Playback, None
        self.assert_all_subsets_divide_correctly(route_name, False)


    def test_get_unbound_recordings(self):
        route_name, api_info = APIRelation.BIND_RECORDING, None
        unbound_rec_info = self.PoolFactory.get_unbound_recordings()
        self.assertGreater(len(unbound_rec_info), 20, "There where less than 20 unbound recordings")


    def test_get_unbound_recordings_distributed(self):
        route_name, api_info = APIRelation.BIND_RECORDING, None
        self.assert_all_subsets_divide_correctly(route_name, False)


    def test_get_unscheduled_schedule_guid_pool(self):
       route_name, api_info = "Unscheduled Schedule GUIDS", None
       schedule_guids = self.PoolFactory.get_unscheduled_schedule_guid_pool("DEV2")
       self.assertGreater(len(schedule_guids), 100, "Not enough unschedule schedule guids were recieved")




    #def test_get_uncheduled_schedule_guid_distributed(self):
    #    route_name, api_info = "Unscheduled Schedule GUIDS", None
    #    self.assert_all_subsets_divide_correctly(route_name, False)
# class TestInverseStateRequestPool(LocustTest):
#
#     #Edits Made -- TODO:: Create User that can have rules constatnly edited
#     def test_create_rules_v1(self):
#         url, datapool = self.get_url_and_pool("Create Rules", 1)
#         datapool.init_normal_pool(self.dev2conn)
#         self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
#         json_post = datapool.get_json()
#         response = requests.post(url, json=json_post)
#         self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
#
#     def test_create_rules_v4(self):
#         url, datapool = self.get_url_and_pool("Create Rules", 4)
#         datapool.init_normal_pool(self.dev2conn)
#         self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
#         json_post = datapool.get_json()
#         response = requests.post(url, json=json_post)
#         self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
#
#
#
#     #Edits Made -- TODO:: Create User that can have rules constatnly deleted
#     def test_delete_rules_v1(self):
#         url, datapool = self.get_url_and_pool("Delete Rules", 1)
#         datapool.init_normal_pool(self.dev2conn)
#         self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
#         json_post = datapool.get_json()
#         response = requests.post(url, json=json_post)
#         self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
#
#
#     #Edits Made -- TODO: Create Users to constantly add recordings too and add appropriate WHERE Clause to SQL statements
#     def test_create_recordings_v1(self):
#         url, datapool = self.get_url_and_pool("Create Recordings", 1)
#         datapool.init_normal_pool(self.dev2conn)
#         self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
#         json_post = datapool.get_json()
#         response = requests.post(url, json=json_post)
#         self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
#
#
#     def test_create_recordings_v4(self):
#         url, datapool = self.get_url_and_pool("Create Recordings", 4)
#         datapool.init_normal_pool(self.dev2conn)
#         self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
#         json_post = datapool.get_json()
#         response = requests.post(url, json=json_post)
#         self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
#
#
#
#     #Edits Made -- TODO:: Create Users to constantly add and delete from -- add appropriate WHERE Clasue to SQL statemetns
#     def test_delete_recordings_v1(self):
#         url, datapool = self.get_url_and_pool("Delete Recordings", 1)
#         datapool.init_normal_pool(self.dev2conn)
#         self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
#         json_post = datapool.get_json()
#         response = requests.post(url, json=json_post)
#         self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)

