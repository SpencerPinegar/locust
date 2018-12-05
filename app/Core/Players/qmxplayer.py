import json
import math

from collections import namedtuple

from app.Core.exceptions import CodecNotFound, QMXPlaylistNoStreams
from app.Core.Players.baseplayer import BaseManifest, BasePlayer, MediaPlaylist
from app.Utils.utils import to_sized_hex




# QVT Keys
PLAYBACK_INFO_KEY = "playback_info"
QVT_CLIP_LIST_KEY = "clips"

# Manifest Keys
LOCATION_KEY = "location"
START_OFFSET_KEY = "start_offset"
STOP_OFFSET_KEY = "stop_offset"
TYPE_KEY = "type"

# Playlist Keys
Segment_Info_Key = "segment_info"
Duration_Key = "duration"
First_Segment_Num_Key = "start"
Last_Segment_Num_Key = "stop"
URL_Info_Key = "pattern"

Stream_Key = "streams"
ID_Key = "id"
Video_Key = "video"
Audio_Key = "audio"
Bitrate_Key = "bitrate"
Codec_Key = "codec"
Codec_Type_Key = "type"

# URL KEYS
PROFILE_REPLACE_KEY = '$profile%02x$'
INDEX_REPLACE_KEY = '$number%08x$'
PARTIAL_REPLACE_KEY = '$partial%s$'


class QMXManifest(BaseManifest):
    CLIPLIST_KEY_SEQUENCE = [PLAYBACK_INFO_KEY, QVT_CLIP_LIST_KEY]
    QMX_MANIFEST_TYPE = "QMX"

    def __init__(self, url, player, quality=0, codecs=[]):
        BaseManifest.__init__(self, QMXManifest.QMX_MANIFEST_TYPE, url, quality, codecs, player)

    def parse(self, content):
        """
        How the manifest info should be parsed if a successful download occurs
        :param content: The content from the url download
        :return:
        """
        content = json.loads(content)
        for key in QMXManifest.CLIPLIST_KEY_SEQUENCE:
            content = content[key]
        clips = content
        processed_clips = []
        for clip in clips:
            clip_type = clip[TYPE_KEY]
            if clip_type != "content":
                print("huh")
            start_offset = clip[START_OFFSET_KEY]
            stop_offset = clip[STOP_OFFSET_KEY]
            url = clip[LOCATION_KEY]
            processed_clips.append(QMXPlaylist(url, clip_type, start_offset, stop_offset, self))
        self._asset_periods = processed_clips

class QMXPlaylist(MediaPlaylist):

    @property
    def seg_name(self):
        """
        Convience property to quickly grab the segment name based on the parent etc....
        :return:
        """
        return "{type} Playlist Segment ({url})".format(type=self._parent_manifest._type, url=self._url)

    @property
    def id_hex(self):
        """
        Returns the stream_id (based on selected stream) as a 2 digit hex with no prefix
        :return: 2 digit hex
        """
        return to_sized_hex(self._stream_id, 2)

    @property
    def current_index(self):
        """
        Returns the current segment index as a 8 digit hex with no prefix
        :return: 8 digit hex
        """
        current_index = self._first_seg_index + self._segments_seen
        return to_sized_hex(current_index, 8)

    def __init__(self, base_url, type, start_offset, end_offset, manifest):
        MediaPlaylist.__init__(self, base_url, manifest)
        self._start_offset = start_offset
        self._end_offset = end_offset
        self.type = type
        self._stream_id = None
        self._period_sort_key = start_offset

    def _request_media_fragment(self):
        """
        Requests the next segment of the stream and verifies it was downloaded successful (will retry if not);
        this method fires locust events so all information can be seen through locust UI
        :return:
        """
        #Set up requesting the media frament
        request_url = self._url.replace(PROFILE_REPLACE_KEY, self.id_hex). \
            replace(INDEX_REPLACE_KEY, self.current_index).replace(PARTIAL_REPLACE_KEY, "")
        reqeust_name = self.seg_name
        byte_request_size = math.floor(self._byte_size / 3)
        headers_1 = {"Range": "bytes=0-{}".format(int(byte_request_size))}
        second_end = byte_request_size * 2 + 1
        headers_2 = {"Range": "bytes={}-{}".format(int(byte_request_size + 1), int(second_end))}
        headers_3 = {"Range": "bytes={}-".format(int(second_end + 1))}
        resp_1 = None
        resp_2 = None
        resp_3 = None
        tries = 0
        success = True
        while not resp_1 or not resp_2 or not resp_3:
            if tries >= MediaPlaylist.SEGMENT_RETRIES:
                success = False
                break
            else:
                resp_1 = self.request(reqeust_name, url=request_url, headers=headers_1)
                resp_2 = self.request(reqeust_name, url=request_url, headers=headers_2)
                resp_3 = self.request(reqeust_name, url=request_url, headers=headers_3)
                tries += 1
        return success


    def parse(self, content):
        """
        How the data from a succesful download is to be parsed and stored locally
        :param content: The content response from the url download
        """
        content = json.loads(content)
        self._set_segment_info(content)
        self._set_stream_info(content, self.wanted_quality, self.wanted_codecs)

    ###################################################################################################################
    ############################ PARSE HELPER METHODS #################################################################
    ###################################################################################################################

    def _set_segment_info(self, json_content_of_items):
        """
        Helper method that parses out the segment info and stores it as an instance variable
        :param json_content_of_items: The json content from the url
        """
        seg_info = json_content_of_items[Segment_Info_Key]
        self._seg_duration = float(seg_info[Duration_Key]) / float(1000)
        self._url = self._url.replace("index.qmx", "") + seg_info[URL_Info_Key]
        first_seg = seg_info[First_Segment_Num_Key]
        first_seg = int((self._start_offset / self._seg_duration)) + int(first_seg) + 1 #TODO: Find if first segment has issue (remove the + 1) or not
        self._first_seg_index = int(first_seg)
        self._total_segments = int((self._end_offset - self._start_offset) / self._seg_duration)

    def _set_stream_info(self, json_content_of_items, quality, wanted_codecs):
        """
        Helper parse method that parses out the streams from the json content and selects the best stream
        and stores it as an instance var
        :param json_content_of_items: The json content from the url
        :param quality: The relative quality index (0 is best, N is worst)
        :param wanted_codecs: list of wanted codecs you want each stream to have (2 max in the list
        """
        StreamInfo = namedtuple("StreamInfo", ["byte_rate", "codecs", "id"])
        stream_info = json_content_of_items[Stream_Key]
        processed_stream = []
        if not stream_info:
            raise QMXPlaylistNoStreams()
        for stream in stream_info:
            bitrate = self.__get_segment_byte_rate(stream)
            codecs = self.__get_codecs(stream)
            str_id = stream[ID_Key]
            processed_stream.append(StreamInfo(bitrate, codecs, str_id))

        media = self.__select_stream(processed_stream, wanted_codecs, quality)
        self._stream_id = media.id
        self._byte_size = media.byte_rate

    ###################################################################################################################
    ################################### HELPERS TO THE HELPER METHODS #################################################
    ###################################################################################################################
    def __get_segment_byte_rate(self, stream):
        """
        Calculates the number of bytes per segment based on the audio and video stream
        :param stream: The stream info json
        :return: (int) the number of bytes per segment
        """
        audio_kbs = stream[Audio_Key][Bitrate_Key]
        video_kbs = stream[Video_Key][Bitrate_Key]
        bits_per_second = (audio_kbs + video_kbs) * 2.048 / float(8)
        return bits_per_second

    def __get_codecs(self, stream):
        """
        Aggregates the codecs used in the audio/video stream
        :param stream: The stream info json
        :return: [string, string] - a list of codecs used by the stream
        """
        audio_codec = stream[Audio_Key][Codec_Key]
        video_codec = stream[Video_Key][Codec_Key][Codec_Type_Key]
        return [audio_codec, video_codec]

    def __select_stream(self, streams, codecs, quality):
        """
        Selects the stream that works with the quality and codecs
        :param streams: The streams from the info json
        :param codecs: The codecs you want to use (can be an empty list for none)
        :param quality: The relative quality of the stream (0 is best, N is worst)
        :return: The selected stream
        """
        if codecs:
            codecs = set(codecs)
            contains_codecs = []
            for stream in streams:
                if codecs <= set(stream.codecs):
                    contains_codecs.append(stream)
            if not contains_codecs:
                raise CodecNotFound("{codecs} not found in manifest url ({url})"
                                    .format(codecs=str(codecs), url=self._parent_manifest._url))
            else:
                return self.__select_stream_with_quality(contains_codecs, quality)
        else:
            return self.__select_stream_with_quality(streams, quality)

    def __select_stream_with_quality(self, streams, quality):
        """
        Selects the best stream based on only the quality (helps the __select_stream method)
        :param streams: The streams in question
        :param quality: The relative quality index (0 is best, N is worst)
        :return: The selected stream
        """
        streams.sort(key=lambda x: x.byte_rate, reverse=True)
        try:
            the_stream = streams[quality]
        except IndexError:
            the_stream = streams[-1]
        return the_stream


class QMXPlayer(BasePlayer):
    PLAYER_TYPE_NAME = "QMX"

    """
    This is the client that plays the HLS Version 3 information based off a asset URL
    It must be ran with the play() method
    It keeps track of each request through the Locust framework events.
    It also tracks a few key performance metrics -
        Initial Buffer Fill - the time difference between when the player starts buffering and starts playing
        Request Information

    """

    def _setup(self, clip_list, quality, codecs, player):

        # download and parse master playlist -- This is the equivelent to a user pressing play
        # This will throw an error if a playable video and audio stream are not found
        qmx_manifest = QMXManifest(clip_list, player, quality, codecs)
        qmx_manifest.download()
        self._manifest = qmx_manifest


    def __init__(self):
        BasePlayer.__init__(self, QMXPlayer.PLAYER_TYPE_NAME)



    def did_load_buffer(self):
        return self._manifest.download()


    def play(self, url, title, quality=0, duration=None, process_qvt=False, codecs=[]):
        #YOU CANNOT PROCESS THE QVT WITH THIS PLAYER
        return super(QMXPlayer, self).play(url, title, quality, duration, False, codecs)

