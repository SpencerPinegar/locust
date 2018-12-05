from app.Utils.locust_test import LocustTest
from app.Utils.route_relations import PlaybackRoutesRelation


class TestPlaybackLocustSingleCore(LocustTest):

    def test_top_n_channels_playback_hls(self):
        self._test_undistributed_playback(PlaybackRoutesRelation.Top_N_Playback, "HLS", 0)

    def test_top_n_channels_playback_dash(self):
        self._test_undistributed_playback(PlaybackRoutesRelation.Top_N_Playback, "DASH", 0)

    def test_top_n_channels_playback_qmx(self):
        self._test_undistributed_playback(PlaybackRoutesRelation.Top_N_Playback, "QMX", 0)

    def test_recent_playback_hls(self):
        self._test_undistributed_playback(PlaybackRoutesRelation.Playback, "HLS", 0)

    def test_recent_playback_dash(self):
        self._test_undistributed_playback(PlaybackRoutesRelation.Playback, "DASH", 0)

    def test_recent_plaback_qmx(self):
        self._test_undistributed_playback(PlaybackRoutesRelation.Playback, "QMX", 0)

class TestPlaybackLocustMultiCoreUndistributed(LocustTest):

    def test_top_n_channels_playback_hls(self):
        self._test_multi_core_undistributed_playback(PlaybackRoutesRelation.Top_N_Playback, "HLS", 0)

    def test_top_n_channels_playback_dash(self):
        self._test_multi_core_undistributed_playback(PlaybackRoutesRelation.Top_N_Playback, "DASH", 0)

    def test_top_n_channels_playback_qmx(self):
        self._test_multi_core_undistributed_playback(PlaybackRoutesRelation.Top_N_Playback, "QMX", 0)

    def test_recent_playback_hls(self):
        self._test_multi_core_undistributed_playback(PlaybackRoutesRelation.Playback, "HLS", 0)

    def test_recent_playback_dash(self):
        self._test_multi_core_undistributed_playback(PlaybackRoutesRelation.Playback, "DASH", 0)

    def test_recent_playback_qmx(self):
        self._test_multi_core_undistributed_playback(PlaybackRoutesRelation.Playback, "QMX", 0)


class TestPlaybackLocustDistributed(LocustTest):

    def test_top_n_channels_playback_hls(self):
        self._test_multi_core_distributed_playback(PlaybackRoutesRelation.Top_N_Playback, "HLS", 0)

    def test_top_n_channels_playback_dash(self):
        self._test_multi_core_distributed_playback(PlaybackRoutesRelation.Top_N_Playback, "DASH", 0)

    def test_top_n_channels_playback_qmx(self):
        self._test_multi_core_distributed_playback(PlaybackRoutesRelation.Top_N_Playback, "QMX", 0)

    def test_recent_playback_hls(self):
        self._test_multi_core_distributed_playback(PlaybackRoutesRelation.Playback, "HLS", 0)

    def test_recent_playback_dash(self):
        self._test_multi_core_distributed_playback(PlaybackRoutesRelation.Playback, "DASH", 0)

    def test_recent_playback_qmx(self):
        self._test_multi_core_distributed_playback(PlaybackRoutesRelation.Top_N_Playback, "QMX", 0)