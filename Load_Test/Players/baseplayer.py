import gevent
import json
import requests
import urllib3
import time

from locust import events

from Load_Test.exceptions import BufferUnderrun, QVTRequestException
from Load_Test.exceptions import BadContentLength, StaleManifest, StalePlaylist


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LocustRequestObject(object):
    """
    A generic class outlining the default behavior for requests and tracking if they are successful or not through the
    Locust Framework
    """

    ID_LEGNTH = 6

    def __init__(self):
        self._session = None
        self._title = None


    def set_url_request_vars(self, title):
        self._session = requests.Session()
        self._title = title

    def set_as_parent_request_vars(self, parent):
        self._session = parent._session
        self._title = parent._title


    def request(self, name, url=None, headers=None, session=None):
        """
        Defualt method for HTTP requests, verifies each request using content length, returning non if they fail
        :param name: The name of the object making the request
        :return:
        """
        start_time = time.time()

        if url is None:
            url = getattr(self, "_url", None)
        if url is None:
            raise TypeError("No URL was given")
        if not session:
            session = self._session
        try:
            if headers:
                with session:
                    r = session.get(url, verify=False, headers=headers)
            else:
                with session:
                    r = session.get(url, verify=False)
            r.raise_for_status()  # requests wont raise http error for 404 otherwise
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects) as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="GET", name=name,
                                        response_time=total_time, exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            try:
                response_length = int(r.headers['Content-Length'])
            except KeyError:
                response_length = 0
            if response_length != len(r.content):
                e = BadContentLength("content-length header did not match received content length")
                events.request_failure.fire(request_type="GET", name=name,
                                            response_time=total_time,
                                            exception=e)
            events.request_success.fire(request_type="GET", name=str(self._title),
                                        response_time=total_time,
                                        response_length=response_length)
            return r
        return None

    def download(self, name=None):
        """
        Runs the HTTP requests and parse's the data
        :return: Bool - True if requests was succesful
        """
        r = self.request(name)
        if r:
            self.parse(r.text)
            return True
        else:
            return False

    def parse(self, manifest):
        "How the manifest is to be parsed"
        raise NotImplementedError()


class BaseManifest(LocustRequestObject):
    MANIFEST_RETRIES = 1



    def parse(self, manifest):
        """"
        How the manifest is to be parsed - It should return a list of periods, each containing playlist
        """
        raise NotImplementedError()


    @property
    def name(self):
        return "{code} {type} M ({url})".format(code=self._title, type=self._type, url=self._url)


    @property
    def finished(self):
        """
        This is a boolean property that determines if the manifest has been streamed completely
        :return:
        """
        if not self.__setup:
            return None
        if len(self._asset_periods) is 0:
            return True
        if self._asset_periods[0].finished:
            self._asset_periods.pop(0)
            return self.finished
        else:
            return False

    def _set_base_url(self):
        """
        Sets the _base_url property to 'http://{base_url}.com'
        """
        last_relevant_url_index = self._url.find(".com/", 15) + 4
        self._base_url = self._url[:last_relevant_url_index]



    def download(self, name=None):
        """
        The first download sets up the base manifest
        Each download after downloads a ts segment
        :return: Bool - True if requests was succesful
        """
        if not self.__setup:
            retries = 0
            name = self.name
            response = self.request(name, self._url)
            while response is None:
                if retries < BaseManifest.MANIFEST_RETRIES:
                    response = self.request(name, self._url)
                    retries += 1
                else:
                    raise StaleManifest("Requesting - {}".format(name))
            self._set_base_url()
            self.parse(response.content)
            self._asset_periods.sort(key=lambda x: x._period_sort_key, reverse=True)
            self.__setup = True
            return True
        else:
            if not self.finished:
                return self._asset_periods[0].download()


    def __init__(self, manifest_type, url, quality, codecs, player):
        """
        :param manifest_type: The Type of manifest being used
        :param url: The url for the manifest type
        :param quality: the quality (0 is highest, N is lowest)
        :param codecs: A list of wanted codecs (["codec1", "codec2"]) - Max length is 2
        """
        LocustRequestObject.__init__(self)
        self.set_as_parent_request_vars(player)
        self.__setup = False
        self._type = manifest_type
        self._url = url
        self._base_url = None
        self._quality = quality
        self._codecs = codecs

        self._asset_periods = None


class MediaPlaylist(LocustRequestObject):

    LOAD_RETRIES = 1
    SEGMENT_RETRIES = 1

    def parse(self, manifest):
        """
        How the Media playlist is to be parsed if a successful initial download occurs.
        :param manifest:
        :return:
        """
        raise NotImplementedError()

    def _request_media_fragment(self):
        """
        Requests a media fragment from the Media playlist (firing locust events) trying again if it fails,
        if it fails to many times it moves onto the next segment and returns False, else it moves onto the
        next segment and returns True
        :return:
        """
        raise NotImplementedError()

    @property
    def playlist_name(self):
        return "{code} {type} P ({url})".format(code=self._title, type=self._parent_manifest._type, url=self._url)



    @property
    def seg_name(self):
        """
        Convience property to quickly grab the segment name based on the parent etc....
        :return:
        """
        return "{code} {type} S ({url})".format(code=self._title, type=self._parent_manifest._type, url=self._url)


    @property
    def wanted_codecs(self):
        """
        property to get list of wanted codecs
        :return: ([String]) list of codecs names  ["codec_1", "codec_2"]
        """
        return self._parent_manifest._codecs

    @property
    def wanted_quality(self):
        """
        property to get quality index
        :return: (int) quality  0
        """
        return self._parent_manifest._quality


    @property
    def finished(self):
        """
        property to get finished state
        :return: (bool) True if finished
        """
        if self._segments_seen == self._total_segments:
            return True
        else:
            return False

    @property
    def current_index(self):
        """
        property to get current index of playlist, should be used in _request_media_fragment
        :return: (int) current playlist ts segment index
        """
        return self._first_seg_index + self._segments_seen

    def download(self, name=None):
        """
        Sets up the playlist (if needed), tries to load the next media segment (using _request_media_fragment that should
        have been implemented in child class based on the current_index property), finally returns bool if it was able
        to load the next media segment
        :param name:
        :return:
        """
        if not self.__setup:
            retries = 0
            name = self.playlist_name
            response = self.request(name, self._url)
            while response is None:
                if retries < MediaPlaylist.LOAD_RETRIES:
                    response = self.request(name, self._url)
                    retries += 1
                else:
                    raise StalePlaylist("Requesting - {}".format(name))
            self.parse(response.content)
            self.__setup = True
            return self.download()
        else:
            if not self.finished:
                success = self._request_media_fragment()
                self._segments_seen += 1
                return success

    def __init__(self, base_url, manifest):
        LocustRequestObject.__init__(self)
        self.set_as_parent_request_vars(manifest)
        self.__setup = False
        self._parent_manifest = manifest
        self._url = base_url

        self._segments_seen = 0
        self._first_seg_index = None
        self._total_segments = None
        self._seg_duration = None
        self._period_sort_key = None






class BasePlayer(LocustRequestObject):
    """
    This class is a generic base class for different types of locust http streaming clients such as HLS and DASH.
    Children of this class must implement 4 methods to before the play functionality can be used
        1. finished property (bool) - A property that only returns true when the last segment of the video/audio you are
            trying to stream has been requested

        2. segment_duration (float) - A property that returns the length of the current segment in seconds

        3. _load_buffer() - A method that requests a segment stream, firing locust events for each success and
                failure but it should not increment the players total_loaded_buffer instance var

        4. _setup(streaming_asset_url, quality) - A method that processes the streaming URL and sets up the player based
                on the quality (0 is best, N is worst) so _load_buffer can continuously be called until the asset ends.
                This method should fire locust events for the
    """
    NEEDED_BUFFER_TIME_FOR_PLAY = 4  # time to wait before playing
    MAX_BUFFER = 30  # the maximum amount of buffer allowed
    MAX_RETRIES = 2 # the maximum amount of times a stream can be retried
    PAUSE_BETWEEN_SEGMENTS = 1 # default time to wait between context switches after a stream


    def _setup(self, url, quality, codecs, player):
        """
        This method should set up the player to run based off its specific type, it must be implemented in child class
        This method should set the _manifest instance variable to the manifest base type being used
        :param url: The player type expected url string (.m3u8, qvt, etc.)
        :param quality: The quality index (0 is highest, N is lowest)
        """
        raise NotImplementedError()

    def did_load_buffer(self):
        """
        This method should load the stream with requests, firing locust events for each success and failure
        but it should not increment the players total_loaded_buffer instance var, this is done already
        """
        raise NotImplementedError()


    @property
    def needs_buffer(self):
        """
        :return: (bool) true if the player needs to load more buffer

        """
        return (self.total_loaded_buffer - self.time_played) < BasePlayer.MAX_BUFFER


    @property
    def time_played(self):
        """
        :return: (float) the amount of time that has passed since the player started playing
        """
        try:
            return self.end_play_time - self.start_play_time
        except TypeError:
            return 0

    @property
    def finished(self):
        """
        :return: (bool) True if the whole url has been pulled - don't return true if the player has played longer than
        the duration asked to play, that case is handled in the player
        """
        return self._manifest.finished


    @property
    def segment_duration(self):
        """
        :return: (float) the length of time the each _load_buffer action increments the buffer in seconds
        :return:
        """
        if self._seg_duration:
            return self._seg_duration
        else:
            self._seg_duration = self._manifest._asset_periods[0]._seg_duration
            return self._seg_duration


    def __init__(self, type, keys_to_string_url=[], replacement_items=[]):
        LocustRequestObject.__init__(self)
        """
        Initialize the player so it can read/parse any url that works with the type
        :param Type: A string of the player type
        :param keys_to_string_url: The keys to parse out the type url from the QVT JSON response(optional) [key, ...]
        :param replacement_items: Parts of the url string you want replaced Ex: [(to_be_replaced, replacement), ...]
        """
        self.start_buffer_time = None # The time stamp when either the initial player url is processed
        self.start_play_time = None # The time stamp when the player has enough buffer to play
        self.end_play_time = None # The time stamp from the most recent request (eventually the last reqeust)
        self.total_loaded_buffer = 0 # The amount of loaded buffer in seconds
        self.segment_download_times = {} # A dictionary to hold information about the segment downloads

        self.is_playing = False # A boolean that dictates whether the player has started playing
        self.type = type # The Player type as a string (HLS, QMX, DASH)
        self.keys_to_string_url = keys_to_string_url # How to process the qvt
        self.replace = replacement_items # How to process the qvt

        self._manifest = None
        self._seg_duration = None


    def play(self, url, title, quality=0, duration=None, process_qvt=False, codecs=[]):
        """
        After the Properties (finished, segment_duration) and methods (_process_qvt, _setup, _load_buffer) have
        been implemented this method will play the url with the quality index specified (0 is highest, N is largest) for
        the specified duration
        :param url: (String) Either the URL for the qvt, or the specific player url
        :param quality: (Int) The relative quality of the player (0 is highest, N is largest)
        :param duration: (Int) The amount of seconds you want the player to run for
        :param process_qvt: (bool) true if the url ends in .qvt
        :return:
        """
        # SETUP THE PLAYER
        retries = 0
        self.set_url_request_vars(title)
        self.start_buffer_time = time.time()

        # Process the QVT
        if process_qvt:
            url = self._process_qvt(url)

        # Setup the player based on its assumed type
        self._setup(url, quality, codecs, self)

        # Start Requesting Streams
        while True:
            # Try to start streaming, record relevant start/stop playing times
            self._try_start_playing()

            # Try to load more buffer, if buffer is full give thread control of thread to different player
            if self.finished:
                return self.total_loaded_buffer, self.time_played
            elif self.needs_buffer:
                if self.did_load_buffer():
                    self.total_loaded_buffer += self.segment_duration
            else:
                gevent.sleep(self.segment_duration)
                continue

            # Check that the player isn't encountering buffer underrun and close early if past duration
            if self.is_playing:
                # Buffer underun check and handle
                if self.time_played >= self.total_loaded_buffer:
                    if not self.finished:
                        self._report_buffer_over_run()
                        return self.total_loaded_buffer, self.time_played
                # Duration has passed check and handle
                if duration and self.time_played > duration:
                    return self.total_loaded_buffer, self.time_played


    def _process_qvt(self, url):
        """
        Processes the qvt by requesting its URL, and parsing the appropriate streaming url from the json response
        using a sequence of keys entered at initialization. Descriptive Locust events are fired throughout so
        this process can be monitored from the Locust UI
        :param url: The QVT URL
        :return: Specified steaming url (specified with sequeence of keys and replacement tuple.
        """
        name = "QVT LOAD ({url})".format(url=url)
        r = self.request(name, url)
        if r is not None:
            content = json.loads(r.content)
            for key in self.keys_to_string_url:
                try:
                    content = content[key]
                except KeyError:
                    raise KeyError("QVT does not contain the following sequence of keys - {keys}".format(
                        keys=self.keys_to_string_url))
            processed_qvt = content

            for to_replace, replacement in self.replace:
                processed_qvt = content.replace(to_replace, replacement)

            return processed_qvt
        else:
            raise QVTRequestException(str(url) + " QVT URL Could not be loaded")

    @classmethod
    def process_qvt(cls, url, keys_to_string_url, to_replace):
        """
        Processes the qvt by requesting its URL, and parsing the appropriate streaming url from the json response
        using a sequence of keys entered at initialization. Descriptive Locust events are fired throughout so
        this process can be monitored from the Locust UI
        :param url: The QVT URL
        :param keys_to_string_url: A list of keys you want replaced till you reach the qvt field desired
        :param to_replace: A list of tuples you want replaced (assuming return value is string) [("to_be_replaced", "replacer")]
        :return: Specified steaming url (specified with sequeence of keys and replacement tuple.
        """
        name = "QVT LOAD ({url})".format(url=url)
        requester = LocustRequestObject()
        requester.set_url_request_vars("CLASS SESSION")
        r = requester.request(name, url)
        if r is not None:
            content = json.loads(r.content)
            for key in keys_to_string_url:
                try:
                    content = content[key]
                except KeyError:
                    raise KeyError("QVT does not contain the following sequence of keys - {keys}".format(
                        keys=keys_to_string_url))
            processed_qvt = content

            for to_replace, replacement in to_replace:
                processed_qvt = content.replace(to_replace, replacement)

            return processed_qvt
        else:
            raise QVTRequestException(str(url) + " QVT URL Could not be loaded")

    def _try_start_playing(self):
        """
        Checks to see if it should start playing (it should if it has more than enough needed buffer for play),
        if it should start playing,  is_playing is set to true and relevant time stamps are recorded
        :return:
        """
        if not self.is_playing and self.total_loaded_buffer > BasePlayer.NEEDED_BUFFER_TIME_FOR_PLAY:
            self.is_playing = True
            self.start_play_time = time.time()
        else:
            self.end_play_time = time.time()

    def _report_buffer_over_run(self):
        """
        Reports buffer underrun to locust UI
        """
        e = BufferUnderrun('Buffer is empty with files still to download')
        events.request_failure.fire(request_type="GET",
                                    name= "BUFFER UNDER RUN",
                                    response_time=self.time_played,
                                    exception=e)









