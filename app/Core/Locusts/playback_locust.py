from locust import TaskSet, Locust
import gevent
import logging
from app.Core.Players import hlsplayer as HLS, dashplayer as DASH, qmxplayer as QMX
from app.Data.request_pool import RequestPoolFactory
from app.Data.config import Config
from app.Utils.route_relations import PlaybackRoutesRelation
from app.Utils.environment_wrapper import PlaybackEnvironmentWrapper as PlaybackEnv
import locust.stats
#from setproctitle import setproctitle

SECONDS = 1000  # ms in seconds
playback_vars = PlaybackEnv.load_env()
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
#setproctitle("-LOCUST Playback Slave {}".format(playback_vars.slave_index))
logging.info("IMPORTED PLAYBACK SUCCESFULLY")
logging.disable(logging.CRITICAL)

#TODO: Allow VODPlayer to play a resource that is popped from a CSV file containing URL's

def get_client_type(client_type):
    client_type = client_type.upper()
    if str(client_type) == "HLS":
        locust_client = HLS.HLSPlayer()
    elif str(client_type) == "DASH":
        locust_client = DASH.DASHPlayer()
    elif str(client_type) == "QMX":
        locust_client = QMX.QMXPlayer()
    else:
        raise Exception("THIS SHOULD NEVER BE READ")
    return locust_client

class PlaybackBehavior(TaskSet):
    """
    Allow Task-set to be run uniquely for each user asset so no stream is stored in DVR cache twice
    """

    def setup(self):

        logging.info(playback_vars)
        PlaybackBehavior.env = "DEV2" #env_wrapper.get("ENV") - We only want to playback test DEV2 but maybe not forever
        locust.stats.CSV_STATS_INTERVAL_SEC = playback_vars.stat_interval
        config = Config()
        PlaybackBehavior.pool_factory = RequestPoolFactory(config, playback_vars.comp_index, playback_vars.max_comp_index,
                                                           playback_vars.slave_index, playback_vars.max_slave_index,
                                                           playback_vars.size, [PlaybackBehavior.env])

        action = playback_vars.action
        PlaybackBehavior.quality = playback_vars.quality
        PlaybackBehavior.codecs = playback_vars.codecs
        the_relation = self._get_playback_setup_relation()
        the_relation.execute_related(action, playback_vars)


    def playback(self):
        self._play_next()


    def top_n_channels(self):
       self._play_next()


    def _play_next(self):
        if not self.__is_another_qvt():
            logging.info("DONE! Sleeping 1 minute")
            gevent.sleep(60)

            pass
        else:
            asset_info = PlaybackBehavior.qvt_pool.pop()
            logging.info("Title: " + asset_info.title + " Remaining: " + str(len(PlaybackBehavior.qvt_pool)))
            self.client.play(asset_info.url, asset_info.title, quality=PlaybackBehavior.quality, process_qvt=True, codecs=PlaybackBehavior.codecs)


    def _get_playback_setup_relation(self):
        PlaybackBehavior.tasks = [PlaybackBehavior._play_next]
        def playback_setup(opts):
            PlaybackBehavior.qvt_pool = PlaybackBehavior.pool_factory.get_recent_playback_recording(opts.dvr, opts.days,
                                                                                                    opts.user)
        def top_n_channels_setup(opts):
            PlaybackBehavior.qvt_pool = PlaybackBehavior.pool_factory.get_top_n_channels_in_last_day()
        return PlaybackRoutesRelation(playback_setup, top_n_channels_setup)

    def __is_another_qvt(self):
        return len(PlaybackBehavior.qvt_pool) > 0

class PlaybackUser(Locust):
    task_set = PlaybackBehavior
    min_wait = 0 * SECONDS
    max_wait = 0 * SECONDS


    def __init__(self):
        super(Locust, self).__init__()
        self.client = get_client_type(PlaybackEnv.load_env().client)
