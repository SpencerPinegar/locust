from unittest import TestCase
from API_Load_Test.Config.config import Config
from API_Load_Test.request_pool import RequestPoolFactory

class APITest(TestCase):

    def setUp(self):
        self.expected_routes = {"User Recordings Ribbon", "User Franchise Ribbon", "User Recspace Information", "Update User Settings",
                               "Create Recordings", "Protect Recordings", "Mark Watched", "Delete Recordings", "Create Rules", "Update Rules",
                               "Delete Rules", "List Rules"}
        self.expected_api_env = {"DEV1", "DEV2", "DEV3", "QA", "BETA", "BETA2"}
        self.config = Config(debug=False)
        self.PoolFactory = RequestPoolFactory(self.config, envs={"DEV2"})
        self.dev2_host = self.config.get_api_host("DEV2")

    def tearDown(self):
        self.PoolFactory.close()




