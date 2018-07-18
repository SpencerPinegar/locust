from unittest import TestCase
from API_Load_Test.Config.config import Config
from API_Load_Test.request_pool import _ReadOnlyRequestPool, RequestPoolFactory
from API_Load_Test.test.api_test import APITest
import json
import requests
from API_Load_Test.Config.sql_route_statements import TEST_SQL_STATEMENTS

config = Config()

def execute_test_sql_statement(route, env):
    query = TEST_SQL_STATEMENTS[route]
    try:
        with config.get_db_connection(env).cursor() as cur:
            cur.execute(query)
            data = cur.fetchall()
            return data
    except Exception as e:
       raise e




class TestReadOnlyRequestPool(APITest):

    Non_Inited_Data_Pool_Mssg = "The DataPool failed when trying to create normal JSON data -- Check the datapool initlization code"
    Non_200_Post_Mssg = "The JSON Post request was not properly proccessed by the server -- see the relevant network error code"
    Non_Normal_Length_Mssg = "The JSON data size does not reflect a normal user -- see the relevant SQL statement and the Normal Min/Max data in the SETTINGS.yaml file"







    def test_user_recordings_ribbon_v1(self):
        route_name, version = ("User Recordings Ribbon", 1)
        datapool, route = self.PoolFactory.get_user_recordings_ribbon_pool_and_route(version, "DEV2", 30, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        # Must initlize to be valid
        json_post = datapool.get_json()
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
        #this test wont be valid unless we have a 200 response
        response_length = len(json.loads(response.content)["rs_recordings"])
        min_length, max_length = self.config.get_api_route_normal_min_max(route_name)
        self.assertTrue(min_length <= response_length <= max_length, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)


    def test_user_recordings_ribbon_v2(self):
        route_name, version = ("User Recordings Ribbon", 2)
        datapool, route = self.PoolFactory.get_user_recordings_ribbon_pool_and_route(version, "DEV2", 30, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        #Must intilize to be valid
        json_post_post = datapool.get_json()
        response = requests.post(url, json=json_post_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
        # this test wont be valid unless we have a 200 response
        response_len = len(json.loads(response.content)["rs_recordings"])
        min_len, max_len = self.config.get_api_route_normal_min_max(route_name)
        self.assertTrue((min_len <= response_len <= max_len), TestReadOnlyRequestPool.Non_Normal_Length_Mssg)

    def test_user_recordings_ribbon_v4(self):
        route_name, version = ("User Recordings Ribbon", 4)
        datapool, route = self.PoolFactory.get_user_recordings_ribbon_pool_and_route(version, "DEV2", 30, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        # Must inilize to be valid
        json_post_post = datapool.get_json()
        response = requests.post(url, json=json_post_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
        # this test wont be valid unless we have a 200 response
        response_len = len(json.loads(response.content)["rs_recordings"])
        min_len, max_len = self.config.get_api_route_normal_min_max(route_name)
        self.assertTrue(min_len <= response_len <= max_len, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)



    def test_user_recordings_all_normal_data(self):
        route_name, version = ("User Recordings Ribbon", 1)
        datapool, route = self.PoolFactory.get_user_recordings_ribbon_pool_and_route(version, "DEV2", 30, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        for json_post in datapool.normal_pool:
            response = requests.post(url, json=json_post)
            self.assertEqual(200, response.status_code, TestReadOnlyRequestPool)
            resp_len = len(json.loads(response.content)["rs_recordings"])
            min_len, max_len = self.config.get_api_route_normal_min_max(route_name)
            self.assertTrue(min_len <= resp_len <= max_len, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)


    # No Edits done on this API Call -- Good on Data
    #TODO: Make users with params so we know they exist for sure
    def test_user_franchise_ribbon_v1(self):
        route_name, version = ("User Franchise Ribbon", 1)
        datapool, route = self.PoolFactory.get_user_franchise_ribbon_pool_and_route(version, "DEV2", 5, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post_post = datapool.get_json(filter="recorded")
        response = requests.post(url, json=json_post_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
        # this test wont be valid unless we have a 200 response
        resp_len = 0
        for season in json.loads(response.content)['seasons']:
            resp_len += len(season["episodes"])
        min_len, max_len = self.config.get_api_route_normal_min_max(route_name)
        self.assertTrue(min_len <= resp_len <= max_len, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)


    def test_user_franchise_ribbon_v4(self):
        route_name, version = ("User Franchise Ribbon", 4)
        datapool, route = self.PoolFactory.get_user_franchise_ribbon_pool_and_route(version, "DEV2", 5, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post = datapool.get_json(filter="recorded")
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
        # this test wont be valid unless we have a 200 response
        resp_len = 0
        for season in json.loads(response.content)['seasons']:
            resp_len += len(season["episodes"])
        min_len, max_len = self.config.get_api_route_normal_min_max(route_name)
        self.assertTrue(min_len <= resp_len <= max_len, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)

    def test_user_franchise_all_normal_data(self):
        route_name, version = ("User Franchise Ribbon", 1)
        datapool, route = self.PoolFactory.get_user_franchise_ribbon_pool_and_route(version, "DEV2", 30, 60, filter="recorded")
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        for json_post in datapool.normal_pool:
            response = requests.post(url, json=json_post)
            self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
            resp_len = 0
            for season in json.loads(response.content)['seasons']:
                resp_len += len(season["episodes"])
            min_len, max_len = self.config.get_api_route_normal_min_max(route_name)
            self.assertTrue(min_len <= resp_len <= max_len, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)

    #No Edits done on this API Call -- Good on Data
    def test_user_recspace_information_v1(self):
        route_name, version = ("User Recspace Information", 1)
        datapool, route = self.PoolFactory.get_user_recspace_information_pool_and_route(version, "DEV2", 30, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post = datapool.get_json()
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)


    #No Edits Made
    def test_mark_watched_v1(self):
        route_name, version = ("Mark Watched", 1)
        datapool, route = self.PoolFactory.get_mark_watched_pool_and_route(version, "DEV2", 30, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post = datapool.get_json()
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)


    def  test_list_rules_v1(self):
        route_name, version = ("List Rules", 1)
        datapool, route = self.PoolFactory.get_list_rules_pool_and_route(version, "DEV2", 30, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post_post = datapool.get_json()
        response = requests.post(url, json=json_post_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
        amount_of_rules = len(json.loads(response.content)["franchise_rules"])
        min_rules, max_rules = self.config.get_api_route_normal_min_max(route_name)
        self.assertTrue(min_rules <= amount_of_rules <= max_rules, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)



    def test_list_rules_v4(self):
        route_name, version = ("List Rules", 4)
        datapool, route = self.PoolFactory.get_list_rules_pool_and_route(version, "DEV2", 30, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post_post = datapool.get_json()
        response = requests.post(url, json=json_post_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
        amount_of_rules = len(json.loads(response.content)["franchise_rules"])
        min_rules, max_rules = self.config.get_api_route_normal_min_max(route_name)
        self.assertTrue(min_rules <= amount_of_rules <= max_rules, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)


    def test_list_rules_all_normal_data(self):
        route_name, version = ("List Rules", 1)
        datapool, route = self.PoolFactory.get_list_rules_pool_and_route(version, "DEV2", 30, 60)
        url = self.dev2_host + route
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        for json_post in datapool.normal_pool:
            response = requests.post(url, json=json_post)
            self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)
            rule_amount = len(json.loads(response.content)["franchise_rules"])
            min_rules, max_rules = self.config.get_api_route_normal_min_max(route_name)
            self.assertTrue(min_rules <= rule_amount <= max_rules, TestReadOnlyRequestPool.Non_Normal_Length_Mssg)


class TestTwoStateRequestPool(APITest):

    def test_update_user_settings_v1(self):
        route_name, version, env, clean_default, dirty_default = ("Update User Settings", 1, "DEV2", 599, 80085)
        abs_size = len(execute_test_sql_statement(route_name, env))
        self.assertGreater(abs_size, 100)
        pool, route = self.PoolFactory.get_update_user_settngs_pool_and_route(version, env, abs_size, abs_size)
        url = self.dev2_host + route
        self.assertEqual(len(pool.normal_pool), abs_size)
        pool.close(url)
        clean_state = execute_test_sql_statement(route_name, env)
        self.assertEqual(len(clean_state), abs_size) #We should have grabbed all 400 users
        for user in clean_state:
            self.assertEqual(user[1], clean_default)
        pool.flip_state()
        self.assertTrue(pool.current_default_params, pool.start_state_params)
        self.assertEqual(0, pool.index)
        for request in range(abs_size): # range based off number of relevant users
            json = pool.get_json()
            response = requests.post(url, json=json)
            self.assertEqual(response.status_code, 200)
        dirty_state = execute_test_sql_statement(route_name, env)
        self.assertEqual(len(dirty_state), abs_size)
        for user in dirty_state:
            self.assertEqual(user[1], dirty_default)
        for reqeust in range(abs_size):
            json = pool.get_json()
            response = requests.post(url, json=json)
            self.assertTrue(response.status_code is 200)
        reclean_state = execute_test_sql_statement(route_name, env)
        for user in reclean_state:
            self.assertEqual(user[1], clean_default)
        pool.close(url)



    #There are 400 recordings that we can pull from to mark as protected or not
    def test_protect_recordings_v1(self):
        route_name, version, env, clean_default, dirty_default = ("Protect Recordings", 1, "DEV2",  True, False)
        abs_size = len(execute_test_sql_statement(route_name, env))
        self.assertGreater(abs_size, 100)
        pool, route = self.PoolFactory.get_protect_recordings_pool_and_route(version, env, abs_size, abs_size)
        url = self.dev2_host + route
        self.assertEqual(len(pool.normal_pool), abs_size)
        pool.close(url)
        clean_state = execute_test_sql_statement(route_name, env)
        self.assertEqual(len(clean_state), abs_size) #We should have grabbed all 400 recordings
        for recording in clean_state:
            self.assertEqual(recording[1], clean_default)
        pool.flip_state()
        self.assertTrue(pool.current_default_params, pool.start_state_params)
        self.assertEqual(0, pool.index)
        for request in range(abs_size): # range based off number of relevant recordings
            json = pool.get_json()
            response = requests.post(url, json=json)
            self.assertEqual(response.status_code, 200)
        dirty_state = execute_test_sql_statement(route_name, env)
        self.assertEqual(len(dirty_state), abs_size)
        for recording in dirty_state:
            self.assertEqual(recording[1], dirty_default)
        for reqeust in range(abs_size):
            json = pool.get_json()
            response = requests.post(url, json=json)
            self.assertTrue(response.status_code is 200)
        reclean_state = execute_test_sql_statement(route_name, env)
        for recording in reclean_state:
            self.assertEqual(recording[1], clean_default)
        pool.close(url)

    def test_update_rules_v1(self):
        route_name, version, env, clean_default, dirty_default = ("Update Rules", 1, "DEV2", 2, 1)
        abs_size = len(execute_test_sql_statement(route_name, env))
        self.assertGreater(abs_size, 100)
        pool, route = self.PoolFactory.get_update_rules_pool_and_route(version, env, abs_size, abs_size)
        url = self.dev2_host + route
        self.assertEqual(len(pool.normal_pool), abs_size)
        pool.close(url)
        clean_state = execute_test_sql_statement(route_name, env)
        self.assertEqual(len(clean_state), abs_size) #We should have grabbed all 400 recordings
        for recording in clean_state:
            self.assertEqual(recording[0], clean_default)
        pool.flip_state()
        self.assertTrue(pool.current_default_params, pool.start_state_params)
        self.assertEqual(0, pool.index)
        for request in range(abs_size): # range based off number of relevant recordings
            json = pool.get_json()
            response = requests.post(url, json=json)
            self.assertEqual(response.status_code, 200)
        dirty_state = execute_test_sql_statement(route_name, env)
        self.assertEqual(len(dirty_state), abs_size)
        for recording in dirty_state:
            self.assertEqual(recording[0], dirty_default)
        for reqeust in range(abs_size):
            json = pool.get_json()
            response = requests.post(url, json=json)
            self.assertTrue(response.status_code is 200)
        reclean_state = execute_test_sql_statement(route_name, env)
        for recording in reclean_state:
            self.assertEqual(recording[0], clean_default)
        pool.close(url)


class TestInverseStateRequestPool(APITest):

    #Edits Made -- TODO:: Create User that can have rules constatnly edited
    def test_create_rules_v1(self):
        url, datapool = self.get_url_and_pool("Create Rules", 1)
        datapool.init_normal_pool(self.dev2conn)
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post = datapool.get_json()
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)

    def test_create_rules_v4(self):
        url, datapool = self.get_url_and_pool("Create Rules", 4)
        datapool.init_normal_pool(self.dev2conn)
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post = datapool.get_json()
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)



    #Edits Made -- TODO:: Create User that can have rules constatnly deleted
    def test_delete_rules_v1(self):
        url, datapool = self.get_url_and_pool("Delete Rules", 1)
        datapool.init_normal_pool(self.dev2conn)
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post = datapool.get_json()
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)


    #Edits Made -- TODO: Create Users to constantly add recordings too and add appropriate WHERE Clause to SQL statements
    def test_create_recordings_v1(self):
        url, datapool = self.get_url_and_pool("Create Recordings", 1)
        datapool.init_normal_pool(self.dev2conn)
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post = datapool.get_json()
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)


    def test_create_recordings_v4(self):
        url, datapool = self.get_url_and_pool("Create Recordings", 4)
        datapool.init_normal_pool(self.dev2conn)
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post = datapool.get_json()
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)



    #Edits Made -- TODO:: Create Users to constantly add and delete from -- add appropriate WHERE Clasue to SQL statemetns
    def test_delete_recordings_v1(self):
        url, datapool = self.get_url_and_pool("Delete Recordings", 1)
        datapool.init_normal_pool(self.dev2conn)
        self.assertFalse(datapool.max_pool_size is -1, TestReadOnlyRequestPool.Non_Inited_Data_Pool_Mssg)
        json_post = datapool.get_json()
        response = requests.post(url, json=json_post)
        self.assertEqual(200, response.status_code, TestReadOnlyRequestPool.Non_200_Post_Mssg)



















