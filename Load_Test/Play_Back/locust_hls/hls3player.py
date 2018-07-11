import random
import gevent
import time
from locust import events, Locust

import hlserror as hlserror
import hlsobject as hlsobject

BUFFERTIME = 4 # time to wait before playing
MAX_BUFFER = 30 # the maximum amount of buffer allowed
MAXRETRIES = 2
PAUSE_BETWEEN_SEGMENTS = 1

class HLS3Locust(Locust):
    """
    This object will actually simulate the load delivered by a client that reads HLS version 3
    It is the exact same as the HLS Locust except the client (See HLS3Player object) making the HTTP requests has been
    customized to accept HLS Version 3 input
    """
    def __init__(self, *args, **kwargs):
        super(HLS3Locust, self).__init__(*args, **kwargs)
        self.client = HLS3Player()

class HLS3Player():
    """
    This is the client that plays the HLS Version 3 information based off a asset URL
    It must be ran with the play() method
    It keeps track of each request through the Locust framework events.
    It also tracks a few key performance metrics -
        Initial Buffer Fill - the time difference between when the player starts buffering and starts playing
        Request Information

    """
    def __init__(self):
        self.start_buffer_time = None #Time of initial master manifest request -- used to calculate initial buffer time
        self.start_play_time = None #Time when first image can be displayed on screen -- used to calculate intiial buffer
        self.end_play_time = None #
        self.total_loaded_buffer = 0
        self.segment_download_times = {} #Used to track info about segment downloads

    def play(self, url=None, quality=None, duration=None, verbose=False):
        #TODO: implement verbose feature
        """
        This method does all the work for the HLS3Player, initially it grabs all the necessary resources from the URL
        and organizes them into a Master Playlist which consists of MediaPlaylists for the resource. Each Media Playlist
        corresponds to a bit-rate. Based on the bit-rate you choose the Mediaplaylist segments are played.
        Successful and Failing requests are logged thorugh the Locust framework
        :param url: The URL of the resource you want to play
        :param quality: The specified Bitrate
        :param duration: How long you want the test to run for
        :param verbose:allow the console to print out information regarding the requests
        :return:
        """

        # download and parse master playlist -- This is the equivelent to a user pressing play
        self._set_start_buffer_time()
        self.master_playlist = hlsobject.MasterPlaylist('master',url)
        master_playlist_request_result_bool = self.master_playlist.download()
        if master_playlist_request_result_bool is False:
            return

        if len(self.master_playlist.media_playlists) == 0:
            # in this case we looked for media playlists, but didn't find any.
            # maybe we're looking at a stream that only has a single bitrate
            # and all the fragments are in the master playlist
            playlist = hlsobject.MediaPlaylist('media',url)
        else:
            # I randomly pick a quality, unless it's specified...
            if quality is None:
                playlist = random.choice(self.master_playlist.media_playlists)
            else:
                i = quality%len(self.master_playlist.media_playlists)
                playlist = self.master_playlist.media_playlists[i]

        # download and parse media playlist
        playlist_request_result_bool = playlist.download()
        last_manifest_time = time.time()
        if playlist_request_result_bool is False:
            return

        # serves as an index for the fragments
        segment_index = playlist.first_media_sequence()

        retries = 0
        playing = False

        while True:



            #Check to see if we should start playing
            if not playing and self.total_loaded_buffer > BUFFERTIME:
                # should we start playing?
                playing = True
                self._set_start_playtime()
            else:
                self._set_end_playtime()


            # Should we load
            if self._load_more_buffer():


                if segment_index <= playlist.last_media_sequence():
                    try:
                        current_media_fragment = playlist.get_media_fragment(segment_index)
                    except hlserror.MissedFragment as e:
                        events.request_failure.fire(request_type="GET",
                                                    name=playlist.url,
                                                    response_time=self._time_played(),
                                                    exception=e)
                        return (self.total_loaded_buffer,self._time_played())

                    self._set_segement_load_start(segment_index)
                    request_result_bool = current_media_fragment.download()
                    if request_result_bool == True:
                        self._set_segement_load_finish(segment_index)
                        self._media_fragment_buffer(current_media_fragment)
                        segment_index+=1
                    else:
                        # TODO, think about this, if I fail to download a single
                        # segment enough times I stop playing. Should I not keep
                        # playing until I run out of buffer then 'buffer underrun'?
                        retries +=1
                        if retries >= MAXRETRIES:
                            return (self.total_loaded_buffer, self._time_played())

            else:
                gevent.sleep(2)
                continue





            if playing:
                # should we grab a new manifest?
                if not playlist.endlist: # only update manifest on live
                    manifest_age = (time.time() - last_manifest_time)
                    if manifest_age > playlist.targetduration*2:  # vlc does this
                        request_result_bool = playlist.download()
                        if request_result_bool == True:
                            last_manifest_time = time.time()





                if self._time_played() >= self.total_loaded_buffer:
                    if segment_index <= playlist.last_media_sequence():
                        # we've run out of buffer but we still have parts to
                        # download
                        e = hlserror.BufferUnderrun('Buffer is empty with '
                                                    'files still to download')
                        events.request_failure.fire(request_type="GET",
                                                    name=playlist.url,
                                                    response_time=self._time_played(),
                                                    exception=e)
                        return (self.total_loaded_buffer, self._time_played())

                    if playlist.endlist:
                        # we've finished a vod (or live stream ended)
                        return (self.total_loaded_buffer, self._time_played())

                    else:
                        # we've downloaded and played all the fragments, but
                        # we've not been told that the stream has finished
                        e = hlserror.StaleManifest('Buffer is empty with no '
                                                   'new files to download.')
                        events.request_failure.fire(request_type="GET",
                                                    name=playlist.url,
                                                    response_time=self._time_played(),
                                                    exception=e)
                        return (self.total_loaded_buffer, self._time_played())
                if duration and self._time_played() > duration:
                    # TODO: Allow the player to restart streaming the same resource if self._time_played() is less than the specified duration
                    # End HLS Stream early based on the duration parameter entered.
                    return (self.total_loaded_buffer, self._time_played())



    def _set_start_buffer_time(self):
        """
        initializes the time the buffer was started
        """
        self.start_buffer_time = time.time()


    def _set_start_playtime(self):
        """
        initializes the time the player was started
        """
        self.start_play_time = time.time()


    def _set_end_playtime(self):
        """
        sees how long the player has been running for
        """
        self.end_play_time = time.time()

    def _set_segement_load_start(self, seg_num):
        """
        initlizes data for segment data request
        :param seg_num: The segment number for the data we are recording
        """
        self.segment_download_times.setdefault(seg_num, {"start time": time.time(), "end time": None})

    def _set_segement_load_finish(self, seg_num):
        """
        records the end time of a segment data request
        :param seg_num: The segment number for the data we are recording
        """
        self.segment_download_times[seg_num]["end time"] = time.time()

    def _media_fragment_buffer(self, media_frag):
        """
        Records how much buffer we have loaded based on the media fragment
        :param media_frag: The media fragment we just loaded
        """
        self.total_loaded_buffer += media_frag.duration

    def _time_played(self):
        """
        See how long the player has been playing for
        :return: INT - the duration the player has been playing for
        """
        try:
            return self.end_play_time - self.start_play_time
        except TypeError:
            return 0

    def _load_more_buffer(self):
        """
        Should the player load more data into the buffer
        :return: Bool - True if it should load more
        """
        try:
            if self.total_loaded_buffer - self._time_played() < MAX_BUFFER:
                return True
            else:
                return False
        except TypeError:
            return True



    def read_stats(self):
        """
        Prints the stats about the recording playback
        """
        print("Start Buffer Time: {0}".format(self.start_buffer_time))
        print("Start Play Time: {0}".format(self.start_play_time))
        print("End Play Time: {0}".format(self.end_play_time))
        print("Total Loaded Buffer: {0}".format(self.total_loaded_buffer))
        print("Play time {0}".format(self.end_play_time - self.start_play_time))
        print("Initial Buffer Fill: {0}".format(self.start_play_time - self.start_buffer_time))
        for segment, details in self.segment_download_times.iteritems():
            if details["end time"] == None:
                print("Segment: {0}: Failed".format(segment))
            else:
                print("Segment: {0}, Downlaod Time:{1}".format(segment, (details["end time"] - details["start time"])))




