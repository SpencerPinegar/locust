from unittest import TestCase
from Load_Test.Data.config import Config
from Load_Test.Data.data_factory import DataFactory

class TestDataFactory(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = Config()

    def setUp(self):
        self.data_factory = DataFactory(TestDataFactory.config)


    def test_users_exist_no_desc(self):
        user_exist = self.data_factory.users_count("DEV2")
        self.assertGreater(user_exist, 100, "There should be over 100 users in the given db")

    def test_users_exist_no_users_with_desc(self):
        user_exist = self.data_factory.users_count("DEV2", "not a real description lololololol123")
        self.assertEqual(user_exist, 0, "A user has the given description?!? -- double check the db")

    def test_user_exist_no_desc_with_max(self):
        correct_amount_of_users_exist = self.data_factory.users_count("DEV2")
        self.assertNotEqual(0, correct_amount_of_users_exist, "If there is exactly 1 user in the Dev2 db ignore this failure")

    def test_user_recs_exist_rs_no_users_with_desc(self):
        no_user_exist = self.data_factory.recs_exist(1, 300, "DEV2", "not a real desc lo123e2", "rs")
        self.assertListEqual(no_user_exist, [], "A user has the given description?!? -- double check the db")

    def test_user_recs_exist_ls_no_users_with_desc(self):
        no_user_exist = self.data_factory.recs_exist(1, 300, "DEV2", "not a real desc l0234324", "ls")
        self.assertListEqual(no_user_exist, [], "A user has the given description?!? -- double check the db")

    def test_user_recs_exist_both_no_users_with_desc(self):
        no_user_exist = self.data_factory.recs_exist(1, 300, "DEV2", "not a real desc l0234324", "both")
        self.assertListEqual(no_user_exist, [], "A user has the given description?!? -- double check the db")

    #TODO: Create users with description - ribbons-user replace desc in test where neccesary

    def test_user_recs_exist_rs_user_no_max(self):
        min = 200
        user_info = self.data_factory.recs_exist(min, None, "DEV2", "Ed Reuse Write User", "rs")
        for user in user_info:
            self.assertTrue(user[1] < 200, "Incorrectly gave bad user")

    def test_user_recs_exists_rs(self):
        min, max = (100, 200)
        bad_user_info = self.data_factory.recs_exist(min, max, "DEV2", "Ed Reuse Write User", "rs")
        for user in bad_user_info:
            self.assertFalse(min <= user[1] <=max , "Incorrectly gave bad user")

    def test_user_recs_exists_rs_always_true(self):
        min, max = (0, None)
        bad_user_info = self.data_factory.recs_exist(min, max, "DEV2", "Ed Reuse Write User", "rs")
        self.assertTrue(bad_user_info, "This test should never fail")

    def test_user_recs_exists_both_always_true(self):
        min, max = (0, None)
        bad_user_info = self.data_factory.recs_exist(min, max, "DEV2", "Ed Reuse Write User", "both")
        self.assertTrue(bad_user_info, "This test should never fail")


    #TODO: Create tests for franchise recs exist

    def test_rules_exist_no_users_with_desc(self):
        min, max = (0, 1)
        bad_user_info = self.data_factory.rules_exist(min, max, "DEV2", "not a real desc q2314dwf")
        self.assertListEqual(bad_user_info, [], "No users should exist with this description")

    def test_rules_exist_update_rules_user(self):
        min, max = (1, 1)
        bad_user_info = self.data_factory.rules_exist(min, max, "DEV2", "update_user_rules")
        self.assertTrue(bad_user_info, "update_user_rules users should have 1 recording rule")

    def test_create_users(self):
        unused_desc = "asdfjlasdjf;alsdjf;a"
        count = 5
        self.data_factory.delete_users("DEV2", unused_desc, 0)
        self.data_factory.create_users("DEV2", unused_desc, count)
        self.assertEquals(count, self.data_factory.users_count("DEV2", unused_desc), "User Guids unsuccessfully created")
        self.data_factory.delete_users("DEV2", unused_desc, 0)
        self.assertEquals(self.data_factory.users_count("DEV2", unused_desc), 0, "User Guids unsuccessfully deleted")


    def test_create_rules_no_users_with_desc(self):
        unused_desc, count, env = ("not_used_loldkas", 5, "DEV2")
        self.data_factory.create_rules(env, unused_desc, count)
        self.assertEqual(0, self.data_factory.users_count(env, unused_desc), "There are users with this description")

    def test_create_rules_newly_created_users(self):
        unused_desc, count, env = ("not_used_lolsafsd", 4, "DEV2")
        self.data_factory.delete_users(env, unused_desc, 0)
        self.assertEqual(0, self.data_factory.users_count(env, unused_desc), "There are users with this description")
        self.data_factory.create_users(env, unused_desc, 4)
        self.assertEqual(count, self.data_factory.users_count(env, unused_desc), "Your users where not correctly created")
        self.data_factory.create_rules(env, unused_desc, count)
        self.assertTrue(self.data_factory.rules_exist(count, count, env, unused_desc), "Your rules where not created properly")
        self.data_factory.delete_rules(env, unused_desc, 0)
        self.assertTrue(self.data_factory.rules_exist(0,0, env, unused_desc), "Your rules where not correctly deleted")
        self.data_factory.delete_users(env, unused_desc, 0)
        self.assertEqual(self.data_factory.users_count(env, unused_desc), 0, "Your users where not correctly deleted")


    def test_create_rules_users_with_rules(self):
        unused_desc, count, env = ("unused_thisasdfasdf", 4, "DEV2")
        self.data_factory.delete_users(env, unused_desc, 0)
        self.assertEqual(0, self.data_factory.users_count(env, count), "There are users with this description")
        self.data_factory.create_users(env, unused_desc, count)
        self.assertEqual(count, self.data_factory.users_count(env, unused_desc), "unsuccessfully created users")
        self.data_factory.create_rules(env, unused_desc, count)
        self.assertTrue(self.data_factory.rules_exist(count, count, env, unused_desc), "unsuccessfully created initial rules")
        self.data_factory.create_rules(env, unused_desc, count)
        self.assertTrue(self.data_factory.rules_exist(count*2, count*2, env, unused_desc), "unsuccessfully created secondary rules")
        self.data_factory.delete_rules(env, unused_desc, 0)
        self.assertTrue(self.data_factory.rules_exist(0, 0, env, unused_desc), "unsuccessfully deleted all rules")
        self.data_factory.delete_users(env, unused_desc, 0)
        self.assertEqual(0, self.data_factory.users_count(env, unused_desc), "unsuccessfully deleted all users")


    def test_shit(self):
        env, desc = ("DEV2", "QA Quick User")
        #self.data_factory.create_users(env, desc, 5)
        self.data_factory.create_recs(env, desc, 1, "rs")
