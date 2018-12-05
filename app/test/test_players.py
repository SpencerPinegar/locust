from __future__ import generators

import unittest
import random

from app.Data.config import Config
from app.Data.request_pool import RequestPoolFactory
from app.Core.Players import dashplayer as dash, hlsplayer as hls, qmxplayer as qmx, baseplayer as base


def get_dash_manifest_url(url_num):
    asset_info = get_dev2_asset_info(url_num)
    return base.BasePlayer.process_qvt(asset_info.url, dash.DASHPlayer.QVT_KEY_SEQUENCE, dash.DASHPlayer.QVT_REPLACE)

def get_hls_manifest_url(url_num):
    asset_info = get_dev2_asset_info(url_num)
    return base.BasePlayer.process_qvt(asset_info.url, hls.HLSPlayer.QVT_KEY_SEQUENCE, hls.HLSPlayer.QVT_REPLACE)


def get_dev2_asset_info(player_numb=1116):
    config = Config()
    p_factory = RequestPoolFactory(config, 0, 0, 0, 0, None, envs=["DEV2"])
    qmx_pool = p_factory.get_recent_playback_recording(player_numb, 100, 10)
    return random.choice(qmx_pool)

def get_player(type):
    type = type.upper()
    if type == "HLS":
        the_player = hls.HLSPlayer()
    elif type == "DASH":
        the_player = dash.DASHPlayer()
    elif type == "QMX":
        the_player = qmx.QMXPlayer()
    else:
        raise Exception("Invalid player type {}".format(type))
    the_player.set_url_request_vars(type + " TEST")
    return the_player


class TestManifests(unittest.TestCase):

    def test_dash_base_manifest_basic(self):
        url = get_dash_manifest_url(1110)
        player = get_player("DASH")
        manifest = dash.DashManifest(url, player)
        manifest.download()
        for playlist in manifest._asset_periods:
            playlist.download()
            playlist.download()



    def test_hls_base_manifest_basic(self):
        url = get_hls_manifest_url(1119)
        player = get_player("HLS")
        manifest = hls.HLSManifest(url, player)
        manifest.download()
        for playlist in manifest._asset_periods:
            playlist.download()
            playlist.download()


    def test_qmx_base_manifest_baseic(self):
        asset_info = get_dev2_asset_info(1116)
        player = get_player("QMX")
        player.set_url_request_vars("QMX TEST")
        manifest = qmx.QMXManifest(asset_info.url, player)
        manifest.download()
        for playlist in manifest._asset_periods:
            playlist.download()
            playlist.download()


class TestPlayers(unittest.TestCase):

    class UnImplemtedPlayer(base.BasePlayer):
        pass

    def test_raises_unimplemnted(self):
        player = TestPlayers.UnImplemtedPlayer("Unimplemented", dash.DASHPlayer.QVT_KEY_SEQUENCE,
                                                  dash.DASHPlayer.QVT_REPLACE)
        player.set_url_request_vars("TEST")
        asset_info = get_dev2_asset_info()
        with self.assertRaises(NotImplementedError):
            player._setup(asset_info.url, 0, [], player)
        with self.assertRaises(NotImplementedError):
            player.did_load_buffer()

    def test_actual_hls_asset(self):
        asset_info = get_dev2_asset_info()
        duration = 45
        buffer_time, play_time = get_player("HLS").play(url=asset_info.url, title=asset_info.title, duration=duration, quality=0
                                                      , process_qvt=True)
        self.assertGreater(play_time, duration)

    def test_full_hls_asset(self):
        asset_info = get_dev2_asset_info()
        old_buffer = base.BasePlayer.MAX_BUFFER
        base.BasePlayer.MAX_BUFFER = 60 * 60 * 3  # 3 hour max buffer
        buffer_time, play_time = get_player("HLS").play(url=asset_info.url, title=asset_info.title, process_qvt=True)
        base.BasePlayer.MAX_BUFFER = old_buffer


    def test_actual_dash_asset(self):
        asset_info = get_dev2_asset_info()
        buffer_time, play_time = get_player("DASH").play(url=asset_info.url, title=asset_info.title, duration=45, process_qvt=True)



    def test_full_dash_asset(self):
        asset_info = get_dev2_asset_info()
        old_buffer = base.BasePlayer.MAX_BUFFER
        base.BasePlayer.MAX_BUFFER = 60 * 60 * 3 # 3 hour max buffer
        buffer_time, play_time = get_player("DASH").play(url=asset_info.url, title=asset_info.title, process_qvt=True)
        base.BasePlayer.MAX_BUFFER = old_buffer



    def test_actual_qmx_asset(self):
        asset_info = get_dev2_asset_info()
        buffer_time, play_time = get_player("QMX").play(url=asset_info.url, title=asset_info.title, duration=45, process_qvt=True)


    def test_full_qmx_asset(self):
        asset_info = get_dev2_asset_info()
        old_buffer = base.BasePlayer.MAX_BUFFER
        base.BasePlayer.MAX_BUFFER = 60 * 60 * 3 # 3 hour max buffer
        buffer_time, play_time = get_player("QMX").play(url=asset_info.url, title=asset_info.title, process_qvt=True)
        base.BasePlayer.MAX_BUFFER = old_buffer
