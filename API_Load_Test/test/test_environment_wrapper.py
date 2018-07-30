from unittest import TestCase
from API_Load_Test.environment_wrapper import EnvironmentWrapper as EnvWrap
import os


class TestEnvironmentWrapper(TestCase):

    UncleanState = "Wrong Information stored in the environment under the 'WRAP_INFO' key"


    def test_init_wrapper_blank_state(self):
        prior = os.environ.get("WRAP_INFO")
        envwrap = EnvWrap(os.environ.copy())
        self.assertEqual(prior, None, TestEnvironmentWrapper.UncleanState)
        self.assertDictEqual(envwrap.info, {}, "No (key, value) pairs where set, no data should be in info")

    def test_init_with_args_string_int_dict(self):
        prior = os.environ.get("WRAP_INFO")
        dict_to_store = {"number": 2, "string": "string2"}
        envwrap = EnvWrap(os.environ.copy(), number=1, string="string1", dict=dict_to_store)
        self.assertEqual(prior, None, TestEnvironmentWrapper.UncleanState)
        self.assertEqual(envwrap.get("number"), 1, "The 'number' kwarg was incorrectly stored")
        self.assertEqual(envwrap.get("string"), "string1", "The 'string' kwarg was incorrectly stored")
        self.assertDictEqual(envwrap.get("dict"), dict_to_store, "The 'dict' kwarg was incorrectly stored")


    def test_init_non_blank_state(self):
        prior = os.environ.get("WRAP_INFO")
        clean_envwrap = EnvWrap(os.environ.copy(), number1=1, string1="one")
        dirt_envwarp = EnvWrap(clean_envwrap.get_env(), number2=2, string2="two")
        self.assertEqual(prior, None, TestEnvironmentWrapper.UncleanState)
        self.assertEqual(dirt_envwarp.get("string1"), "one", "The initial string kwarg was incorrectly stored or transferred")
        self.assertEqual(dirt_envwarp.get("string2"), "two", "The initial string kwarg was incorrectly stored or transferred")
        self.assertTrue(isinstance(dirt_envwarp.get("string1"), str) and isinstance(dirt_envwarp.get("string2"), str),
                        "The Strings were incorrectly converted back to strings")
        self.assertEqual(dirt_envwarp.get("number1"), 1, "The inital number kwarg was incorrectly stored or transferred")
        self.assertEqual(dirt_envwarp.get("number2"), 2, "The second numberkwarg set was incorrectly stored")


    def test_overright_initially_stored_var(self):
        prior = os.environ.get("WRAP_INFO")
        clean_envwrap = EnvWrap(os.environ.copy(), number1=1)
        dirt_envwarp = EnvWrap(clean_envwrap.get_env(), number1=2)
        self.assertEqual(prior, None, TestEnvironmentWrapper.UncleanState)
        self.assertEqual(dirt_envwarp.get("number1"), 2, "The 'number1' kwarg was not overwritted - it should have been")

    def test_get_non_existent_key(self):
        prior = os.environ.get("WRAP_INFO")
        envwrap = EnvWrap(os.environ.copy())
        isnt_var = envwrap.get("not_key")
        self.assertEqual(None, prior, TestEnvironmentWrapper.UncleanState)
        self.assertEqual(isnt_var, None, "Getting unset variables should return None")

    def test_keys(self):
        prior = os.environ.get("WRAP_INFO")
        envwrap = EnvWrap(os.environ.copy(), key1="lol", key2="jk", key5=7)
        self.assertEqual(None, prior, TestEnvironmentWrapper.UncleanState)
        self.assertSetEqual(set(envwrap.keys()), {"key1", "key2", "key5"}, "The keys where incorrectly retrieved")

