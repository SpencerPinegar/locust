from app.Utils.locust_test import LocustTest
from app.Utils.route_relations import RecAPIRoutesRelation

class TestMetaDataUndistributed(LocustTest):

    def test_asset_undistributed(self):
        self._test_undistributed_metadata("Asset", 20, 600)

    def test_airing_undistributed(self):
        self._test_undistributed_recapi("Airing", 20)

class TestMetaDataUndistributedDebug(LocustTest):

    def setUp(self):
        super(TestMetaDataUndistributedDebug, self).setUp()
        self.load_runner.debug = True

    def test_asset_undistributed(self):
        self._test_undistributed_metadata("Asset", 20, 600)

    def test_airing_undistributed(self):
        self._test_undistributed_metadata("Airing", 20)


class TestMetaDataMultiCoreUndistributed(LocustTest):

    def test_asset_multi_core_undistributed(self):
        self._test_multi_core_undistributed_metadata("Asset", 1, 600)


    def test_airing_multi_core_undistributed(self):
        self._test_multi_core_undistributed_metadata("Airing", 20, 600)


class TestMetaDataMultiCoreUndistributedDebug(LocustTest):

    def setUp(self):
        super(TestMetaDataMultiCoreUndistributedDebug, self).setUp()
        self.load_runner.debug = True

    def test_asset_multi_core_undistributed(self):
        self._test_multi_core_undistributed_metadata("Asset", 20, 600)

    def test_airing_multi_core_undistributed(self):
        self._test_multi_core_undistributed_metadata("Airing", 20, 600)
