import urllib3

import xml.etree.ElementTree as ET
from collections import namedtuple

from app.Core.exceptions import (DashManifestMissingPeriods, DashTimeParseIssue, CodecNotFound, StalePlaylist)
from app.Core.Players.baseplayer import BaseManifest, BasePlayer, MediaPlaylist
from app.Utils.utils import to_sized_hex

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Keys to replacek
PLAYBACK_INFO_KEY = "playback_info"
DASH_MANIFEST_URL_KEY = "dash_manifest_url"
REPLACES_X_WITH_Y = ("$encryption_type$", "internal")

# DashManifestKeys
Period_Identifier_Key = "Period"
Segment_Size_Key = "maxSegmentDuration"
Asset_Size_Key = "mediaPresentationDuration"
Is_Audio_Key = "audio"

# Period Keys
Base_URL_Key = "BaseURL"
Adaptation_Set_Key = "AdaptationSet"
Duration_Key = "duration"
Start_Key = "start"
ID_Key = "id"

# Adaptation attribute keys
Codecs_Key = "codecs"
Content_Type_Key = "contentType"
Lange_Key = "lang"
Mime_Type_Key = "mimeType"
Segment_Alignment_Key = "segmentAlignment"
Start_With_SAP_Key = "startWithSAP"
AudioInfo = namedtuple("AudioInfo", ["codecs", "lang"])
# children tag keys
Seg_Temp_Key = "SegmentTemplate"
Representation_Key = "Representation"

# SegmentTemplate attribute Keys
Presentation_Offset_Key = "presentationTimeOffset"
Start_Number_Key = "startNumber"
Time_Scale_Key = "timescale"
Seg_Temp_Duration_key = "duration"
Media_Key = "media"
Initilization_Key = "initialization"

# Representation attribute Keys
Quality_Rank_Key = "qualityRanking"
Frame_Rate_Key = "frameRate"
Height_Key = "height"
Width_Key = "width"
Bandwidth_Key = "bandwidth"
Rep_Codecs_Key = "codecs"
Rep_sar_Key = "sar"
Rep_ID_Key = "id"
Audio_Samp_Key = "audioSamplingRate"


#time assumptions
time_prefix = "PT"
time_suffix = "S"

#mpd stream init replacement key
Stream_Rep_Key = "$RepresentationID$"
Stream_Num_Key = "$Number%08x$"

#Signal strings


def strp_time_dash(time):
    """
    remove any unneccesary characters from time string and format it in seconds
    :param time:  The time string
    :return: A Time float in seconds
    """
    time = str(time).replace(time_prefix, "").replace(time_suffix, "")
    try:
        time = float(time)
    except ValueError as e:
        raise DashTimeParseIssue("Could not parse time value {time} - the assumed prefix is {pre} - the assumed suffix is {suf}".format(time=time, pre=time_prefix,
                                                                                                                                        suf=time_suffix))
    return time




class DashManifest(BaseManifest):
    DASH_MANIFEST_NAME = "DASH"
    """
    The playlist that handles parsing a DASH Manifest
    It assumes that once it has been initially downloaded it will have a functional period that is set up at index 0
    The quality parameter will estimate what we
    """


    def __init__(self, url, player, quality=0, codecs=[]):
        BaseManifest.__init__(self, DashManifest.DASH_MANIFEST_NAME, url, quality, codecs, player)



    def parse(self, manifest):
        """
        Build a xml root from the manifest, build the mediaplaylists, set the asset_period instance var
        :param manifest:
        :re
        """
        root = ET.fromstring(str(manifest))
        self._asset_periods = self.__get_normalized_validated_periods(root)


    def __get_normalized_validated_periods(self, manifest_root):
        periods = []
        for child in manifest_root:
            if Period_Identifier_Key in child.tag:
                new_period = DashPeriod(child, self)
                periods.append(new_period)
        if not periods:
            raise DashManifestMissingPeriods("The Manifest from {url} did not contain periods".format(url=self._url))
        return periods



class DashPeriod(MediaPlaylist):
    MediaStream = namedtuple("MediaStream", ["seg_dur", "time_scale", "start_num", "stream_url_suffix",
                                             "init_url_suffix", "id"])
    Mux = namedtuple("Mux", ["audio", "video"])



    @property
    def current_index(self):
        """
        conveince property to get a mux of the current index's (as 8 digit hex's w/out prefix's) of the audio and
        video stream
        :return: Mux
        """
        video = to_sized_hex(self._first_seg_index.video + self._segments_seen, 8)
        audio = to_sized_hex(self._first_seg_index.audio + self._segments_seen, 8)
        return DashPeriod.Mux(audio, video)


    @property
    def id_hex(self):
        """
        Returns the stream_id (based on selected stream) as a 2 digit hex with no prefix
        :return: Mux of stream id's
        """
        audio = to_sized_hex(self._id.audio, 2)
        video = to_sized_hex(self._id.video, 2)
        return DashPeriod.Mux(audio, video)

    @property
    def stream_url(self):
        """
        A convince method to get the complete current (based on current index) stream url of video and audio stream
        :return:
        """
        index_hex = self.current_index
        audio = self._stream_url.audio.replace(Stream_Num_Key, index_hex.audio)
        video = self._stream_url.video.replace(Stream_Num_Key, index_hex.video)
        return DashPeriod.Mux(audio, video)


    def _request_media_fragment(self):
        urls = self.stream_url
        name = self.seg_name
        audio_url = urls.audio
        audio_name = "Audio " + name
        video_url = urls.video
        video_name = "Video " + name

        audio_success = self._request_media_fragment_helper(audio_url, audio_name)
        video_success = self._request_media_fragment_helper(video_url, video_name)
        return audio_success and video_success


    def _request_media_fragment_helper(self, url, name):
        """
        A helper method for the request media fragment
        :param url: The url of the fragment
        :param name: The name of the fragment request
        :return: If the fragment was successful requested
        """
        success = True
        retries = 0
        resp = self.request(name, url)
        while not resp:
            if retries >= MediaPlaylist.SEGMENT_RETRIES:
                success = False
                break
            else:
                resp = self.request(name, url)
                retries += 1
        return success

    def __init__(self, period_node, manifest):
        super(DashPeriod, self).__init__("", manifest)
        self.__setup = False
        processed_audio_adaptation_sets = []
        processed_video_adaptation_sets = []
        duration = strp_time_dash(period_node.attrib[Duration_Key])
        start    = strp_time_dash(period_node.attrib[Start_Key])
        url = ""
        for child in period_node:
            if Base_URL_Key in child.tag:
                url = manifest._base_url + child.text
            elif Adaptation_Set_Key in child.tag:
                processed_sets = self._process_adaptation_set(child)
                if processed_sets[0].is_video:
                    processed_video_adaptation_sets += processed_sets
                else:
                    processed_audio_adaptation_sets += processed_sets
        audio_stream = self._select_set(processed_audio_adaptation_sets)
        video_stream = self._select_set(processed_video_adaptation_sets)

        self._url             = url
        self._seg_duration    = float(video_stream.seg_dur)/float(video_stream.time_scale)
        self._total_segments  = int(float(duration)/self._seg_duration)
        self._period_sort_key = float(start)

        self._id                = DashPeriod.Mux(audio_stream.id, video_stream.id)
        self._first_seg_index   = DashPeriod.Mux(audio_stream.start_num, video_stream.start_num)

        id_hexs          = self.id_hex
        audio_init_url   = self._url + audio_stream.init_url_suffix.replace(Stream_Rep_Key, id_hexs.audio)
        audio_stream_url = self._url + audio_stream.stream_url_suffix.replace(Stream_Rep_Key, id_hexs.audio)
        video_init_url   = self._url + video_stream.init_url_suffix.replace(Stream_Rep_Key, id_hexs.video)
        video_stream_url = self._url + video_stream.stream_url_suffix.replace(Stream_Rep_Key, id_hexs.video)
        self._stream_url = DashPeriod.Mux(audio_stream_url, video_stream_url)
        self._init_url   = DashPeriod.Mux(audio_init_url, video_init_url)

    def _process_adaptation_set(self, adaptation_set):
        """
        Helper method to process and normalize an adaptation set for video or audio
        :param adaptation_set: The adaptation set you want processed
        :return: A list of normalized adaptation sets
        """
        AdaptationSet = namedtuple("AdaptationSet", ["is_video", "seg_dur", "time_scale", "start_num", "codec",
                                                     "stream_url_suffix", "init_url_suffix", "representations"])
        seg_dur = None
        init_url = None
        stream_url = None
        time_scale = None
        start_num = None
        representations = []
        if adaptation_set.attrib[Content_Type_Key] == Is_Audio_Key:
            is_video = False
            Representation = namedtuple("AudioRepresentaiton", ["bandwidth", "id"])
        else:
            is_video = True
            Representation = namedtuple("VideoRepresentation", ["bandwidth", "id", "codec"])
        for child in adaptation_set:
            if Seg_Temp_Key in child.tag:
                seg_dur = int(child.attrib[Seg_Temp_Duration_key])
                init_url   = child.attrib[Initilization_Key]
                stream_url = child.attrib[Media_Key]
                time_scale = int(child.attrib[Time_Scale_Key])
                start_num = int(child.attrib[Start_Number_Key])
            if Representation_Key in child.tag:
                bandwidth = int(child.attrib[Bandwidth_Key])
                the_id = int(child.attrib[Rep_ID_Key])
                if is_video:
                    codecs = child.attrib[Rep_Codecs_Key]
                    representations.append(Representation(bandwidth, the_id, codecs))
                else:
                    representations.append(Representation(bandwidth, the_id))
        adaptatation_sets = {}
        if is_video:
            Representation = namedtuple("AudioRepresentaiton", ["bandwidth", "id"])
            for rep in representations:
                if rep.codec in adaptatation_sets.keys():
                    old_set = adaptatation_sets[rep.codec]
                    the_reps = [Representation(rep.bandwidth, rep.id)] + old_set.representations
                    new_set = AdaptationSet(is_video, seg_dur, time_scale, start_num, rep.codec, stream_url, init_url,
                                            the_reps)
                    adaptatation_sets[rep.codec] = new_set

                else:
                    the_set = AdaptationSet(is_video, seg_dur, time_scale, start_num, rep.codec, stream_url, init_url,
                                            [Representation(rep.bandwidth, rep.id)])
                    adaptatation_sets[rep.codec] = the_set
            return adaptatation_sets.values()
        else:
            return [AdaptationSet(is_video, seg_dur, time_scale, start_num, adaptation_set.attrib[Codecs_Key],
                                 stream_url, init_url, representations)]

    def _select_set(self, sets_to_choose_from):
        """
        A helper method to select a stream based on codecs (if given) or quality
        :param sets_to_choose_from: A list of Adaptation sets
        :return: All the neccesary info from the chosen stream as a Media stream
        """

        if self.wanted_codecs:
            the_set = None
            for set in sets_to_choose_from:
                if set.codec in self.wanted_codecs:
                    the_set = set
                    the_rep = self.__select_quality(the_set)
                    the_set.representations = the_rep
            if not the_set:
                raise CodecNotFound()
            else:
                return DashPeriod.MediaStream(the_set.seg_dur, the_set.time_scale, the_set.start_num,
                                            the_set.stream_url_suffix, the_set.init_url_siffix,
                                              the_rep.id)
        else:
            return self._trim_representations_to_only_quality(sets_to_choose_from)

    def _trim_representations_to_only_quality(self, sets_to_choose_from):
        """
        A helper method to pick a stream representation based on quality only (no codecs given)
        :param sets_to_choose_from:  A list of AdaptationSets we can choose a stream from
        :return: All needed info from the chosen representation as a Media Stream
        """
        organized_by_spread = []
        for set in sets_to_choose_from:
            set.representations.sort(key=lambda x: x.bandwidth, reverse=True)
            max_band = set.representations[0].bandwidth
            min_band = set.representations[-1].bandwidth
            diff = max_band - min_band
            organized_by_spread.append((diff, set))
        organized_by_spread.sort(key=lambda x : x[0], reverse=True)
        the_set = organized_by_spread[0][1]
        the_rep = self.__select_quality(the_set)
        return DashPeriod.MediaStream(the_set.seg_dur, the_set.time_scale, the_set.start_num,
                                      the_set.stream_url_suffix, the_set.init_url_suffix, the_rep.id)

    def __select_quality(self, set_to_choose_from):
        """
        A helper method that selects the stream from the set based on the quality
        :param set_to_choose_from: A list of stream Representations
        :return: The chosen stream representation
        """
        set_to_choose_from.representations.sort(key=lambda x: x.bandwidth, reverse=True)
        try:
            return set_to_choose_from.representations[self.wanted_quality]
        except IndexError:
            return set_to_choose_from.representations[self.wanted_quality]

    def download(self, name=None):
        """
        OVERWRITTEN METHOD BECASUE TO SETUP THE PLAYLIST WE NEED TO DOWNLOAD 2 ITEMS PRE SETUP and no
        parsing is needed after
        :param name:
        :return:
        """
        if not self.__setup:
            urls = self._init_url
            audio_init_url = urls.audio
            video_init_url = urls.video
            name = self.playlist_name

            retries = 0
            response = self.request(name, audio_init_url)
            while response is None:
                if retries < MediaPlaylist.LOAD_RETRIES:
                    response = self.request(name, audio_init_url)
                    retries += 1
                else:
                    raise StalePlaylist("Requesting - {}".format(name))

            retries = 0
            response = self.request(name, video_init_url)
            while response is None:
                if retries < MediaPlaylist.LOAD_RETRIES:
                    response = self.request(name, video_init_url)
                    retries += 1
                else:
                    raise StalePlaylist("Requesting - {}".format(name))
            self.__setup = True
            return self.download()
        else:
            if not self.finished:
                success = self._request_media_fragment()
                self._segments_seen += 1
                return success


class DASHPlayer(BasePlayer):
    PLAYER_TYPE_NAME = "DASH"
    QVT_KEY_SEQUENCE = [PLAYBACK_INFO_KEY, DASH_MANIFEST_URL_KEY]
    QVT_REPLACE = [REPLACES_X_WITH_Y]
    """
    This is the client that plays the HLS Version 3 information based off a asset URL
    It must be ran with the play() method
    It keeps track of each request through the Locust framework events.
    It also tracks a few key performance metrics -
        Initial Buffer Fill - the time difference between when the player starts buffering and starts playing
        Request Information

    """




    def __init__(self):
        BasePlayer.__init__(self, DASHPlayer.PLAYER_TYPE_NAME, DASHPlayer.QVT_KEY_SEQUENCE, DASHPlayer.QVT_REPLACE)


    def _setup(self, manifest_url, quality, codecs, player):

        # download and parse master playlist -- This is the equivelent to a user pressing play
        # This will throw an error if a playable video and audio stream are not found
        dash_manifest = DashManifest(manifest_url, player, quality, codecs)
        dash_manifest.download()
        self._manifest = dash_manifest


    def did_load_buffer(self):
        return self._manifest.download()
