import os
import yaml
from unittest import TestCase

from Load_Test.Misc.environment_wrapper import (EnvironmentWrapper as EnvWrap, APIEnvironmentWrapper as APIWrap,
                                                PlaybackEnvironmentWrapper as PlaybackWrap,
                                                DistributedLocustEnvironmetWrapper as LocWrap)


class TestEnvironmentWrapper(TestCase):

    UncleanState = "Wrong Information stored in the environment under the 'WRAP_INFO' key"
    dict_to_store = {"number": 2, "string": "string2", "inner_dict": {"int": 3,
                                                                      "string": "hi",
                                                                      "float": 2.3,
                                                                      }
                     }

    def test_init_wrapper_blank_state_update(self):
        prior = os.environ.get(EnvWrap.WRAP_INFO_KEY)
        envwrap = EnvWrap(os.environ.copy(), {}, True)
        self.assertEqual(prior, None, TestEnvironmentWrapper.UncleanState)
        self.assertEqual(envwrap.keys(), [], "No (key, value) pairs where set, no keys should exist")

    def test_init_with_args_string_int_dict_update(self):
        prior = os.environ.get(EnvWrap.WRAP_INFO_KEY)
        envwrap = EnvWrap(os.environ.copy(), TestEnvironmentWrapper.dict_to_store, True)
        self.assertEqual(prior, None, TestEnvironmentWrapper.UncleanState)
        self.assertEqual(envwrap["number"], 2, "The 'number' kwarg was incorrectly stored")
        self.assertEqual(envwrap["string"], "string2", "The 'string' kwarg was incorrectly stored")
        self.assertDictEqual(envwrap["inner_dict"], TestEnvironmentWrapper.dict_to_store["inner_dict"],
                             "The 'dict' kwarg was incorrectly stored")

    def test_init_non_blank_state_no_update(self):
        clean_envwrap = EnvWrap(os.environ.copy(), TestEnvironmentWrapper.dict_to_store, False)
        self.assertEqual(clean_envwrap.keys(), [], "The env wrap updated when it shouldn't have")

    def test_load_non_blank_state_no_update(self):
        prior = os.environ.get(EnvWrap.WRAP_INFO_KEY)
        init_envwrap = EnvWrap(os.environ.copy(), TestEnvironmentWrapper.dict_to_store, True)
        changed_dict = TestEnvironmentWrapper.dict_to_store.copy()["number"] = -30
        should_be_same_as_init_wrap = EnvWrap(init_envwrap.get_env(), changed_dict, False)
        self.assertEqual(prior, None, TestEnvironmentWrapper.UncleanState)

        self.assertEqual(should_be_same_as_init_wrap["number"], 2,
                         "The initial string kwarg was incorrectly overwrittem")
        self.assertEqual(should_be_same_as_init_wrap["string"], "string2",
                         "The initial string kwarg was incorrectly stored or transferred")
        self.assertTrue(isinstance(should_be_same_as_init_wrap["string"], str) and isinstance(should_be_same_as_init_wrap["number"], int),
                        "The Strings were incorrectly converted back to strings")
        self.assertEqual(should_be_same_as_init_wrap["inner_dict"], TestEnvironmentWrapper.dict_to_store["inner_dict"],
                         "The inital number kwarg was incorrectly stored or transferred")


    def test_load_non_blank_state_update(self):
        prior = os.environ.get(EnvWrap.WRAP_INFO_KEY)
        init_envwrap = EnvWrap(os.environ.copy(), TestEnvironmentWrapper.dict_to_store, True)
        changed_dict = TestEnvironmentWrapper.dict_to_store.copy()
        changed_dict["number"] = -30
        changed_dict["inner_dict"]["int"] = 9
        changed_dict["string"] = "string3"
        should_be_same_as_init_wrap = EnvWrap(init_envwrap.get_env(), changed_dict, True)
        self.assertEqual(prior, None, TestEnvironmentWrapper.UncleanState)

        self.assertEqual(should_be_same_as_init_wrap["number"], -30,
                         "The initial int was not updated")
        self.assertEqual(should_be_same_as_init_wrap["string"], "string3",
                         "The initial string was not updated")
        self.assertTrue(isinstance(should_be_same_as_init_wrap["string"], str) and isinstance(should_be_same_as_init_wrap["number"], int),
                        "The Strings were incorrectly converted back to strings")
        self.assertEqual(should_be_same_as_init_wrap["inner_dict"], changed_dict["inner_dict"],
                         "The dict was not updated")

    def test_get_non_existent_key(self):
        prior = os.environ.get(EnvWrap.WRAP_INFO_KEY)
        envwrap = EnvWrap(os.environ.copy(), {}, True)
        isnt_var = envwrap["not_key"]
        self.assertEqual(None, prior, TestEnvironmentWrapper.UncleanState)
        self.assertEqual(isnt_var, None, "Getting unset variables should return None")

    def test_keys(self):
        prior = os.environ.get("WRAP_INFO")
        envwrap = EnvWrap(os.environ.copy(), TestEnvironmentWrapper.dict_to_store, True)
        self.assertEqual(None, prior, TestEnvironmentWrapper.UncleanState)
        self.assertSetEqual(set(envwrap.keys()), set(TestEnvironmentWrapper.dict_to_store.keys()),
                            "The keys where incorrectly retrieved")



class TestDistributedLocustEnv(TestCase):

    def test_load_no_update(self):
        loc_env = LocWrap(2, 1, 1, 2, 2, None, False)
        self.assertEqual(loc_env.stat_interval, None, "Keys unintentially updated")
        self.assertEqual(loc_env.slave_index, None, "Keys unintentially updated")
        self.assertEqual(loc_env.comp_index, None, "Keys unintentially updated")
        self.assertEqual(loc_env.max_slave_index, None, "Keys unintentially updated")
        self.assertEqual(loc_env.max_comp_index, None, "Keys unintentially updated")

    def test_load_update(self):
        loc_env = LocWrap(2, 1, 1, 2, 2, None, True)
        self.assertEqual(loc_env.stat_interval, 2, "Keys unintentially updated")
        self.assertEqual(loc_env.slave_index, 1, "Keys unintentially updated")
        self.assertEqual(loc_env.comp_index, 1, "Keys unintentially updated")
        self.assertEqual(loc_env.max_slave_index, 2, "Keys unintentially updated")
        self.assertEqual(loc_env.max_comp_index, 2, "Keys unintentially updated")

    def test_setters(self):
        loc_env = LocWrap(2, 1, 1, 2, 2, None, True)
        loc_env.slave_index = 0
        loc_env.comp_index = 0
        self.assertEqual(loc_env.stat_interval, 2, "Keys unintentially updated")
        self.assertEqual(loc_env.slave_index, 0, "Keys unintentially updated")
        self.assertEqual(loc_env.comp_index, 0, "Keys unintentially updated")
        self.assertEqual(loc_env.max_slave_index, 2, "Keys unintentially updated")
        self.assertEqual(loc_env.max_comp_index, 2, "Keys unintentially updated")

class TestChildLocustEnv(TestCase):

    def test_creation_loads_values_playback(self):
        play_env = PlaybackWrap("Test", 0, [], "HLS", 20, 12, 1, 2, 0, 0, 0, 0, None)
        our_info = play_env.get_env()[PlaybackWrap.WRAP_INFO_KEY]
        self.assertDictEqual(play_env._options, yaml.safe_load(our_info), "The Env Wrap was not saved correctly")
        os.environ[PlaybackWrap.WRAP_INFO_KEY] = our_info
        play_env_2 = PlaybackWrap.load_env()
        self.assertDictEqual(play_env._options, play_env_2._options, "The Env Wrap was not loaded correctly")

    def test_creation_loads_values_api(self):
        api_env = APIWrap("TEST", 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
        our_info = api_env.get_env()[PlaybackWrap.WRAP_INFO_KEY]
        self.assertDictEqual(api_env._options, yaml.safe_load(our_info), "The Env Wrap was not saved correctly")
        os.environ[PlaybackWrap.WRAP_INFO_KEY] = our_info
        play_env_2 = PlaybackWrap.load_env()
        self.assertDictEqual(api_env._options, play_env_2._options, "The Env Wrap was not loaded correctly")