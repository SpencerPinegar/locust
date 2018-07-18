import random
from locust import TaskSet, task
import hls3player as hlsplayer
import csv

SECONDS = 1000  # ms in seconds

#TODO: Allow VODPlayer to play a resource that is popped from a CSV file containing URL's



class HLS3Behavior(TaskSet):
    """
    Allow Task-set to be run uniquely for each user asset so no stream is stored in DVR cache twice
    """
    url = "NOT_FOUND"

    #def on_start(self):
    #    if len(USER_CREDENTIALS) > 0:
     #       self.url = USER_CREDENTIALS[0]

    def build_url(self):
        self.url ="http://d-gp2-dvrmfs-1111.rd.movetv.com/a29fbac42ae44a0385c879966a74d6d0/internal_master.m3u8#self.url" #make the HLS3Behavior

    @task
    def vod_stream(self):
        self.build_url()
        self.client.play(url = self.url, quality=1)




class HLS3User(hlsplayer.HLS3Locust):
    task_set = HLS3Behavior
    min_wait = 0 * SECONDS
    max_wait = 0 * SECONDS

    def __init__(self):
        super(HLS3User, self).__init__()

    #def __init__(self):
    #    super(HLS3User, self).__init__()
    #    global USER_CREDENTIALS
    #    if USER_CREDENTIALS == None:
    #     with open('dvr_user_asset_info.csv', 'rb') as f:
    #           reader = csv.reader(f)
    #           USER_CREDENTIALS = list(reader)











