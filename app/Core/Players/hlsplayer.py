import time
import urlparse

from locust import events

from app.Utils import cast
from app.Core.exceptions import MissedFragment, CodecNotFound
from app.Core.Players.baseplayer import BaseManifest, BasePlayer, MediaPlaylist, LocustRequestObject

BUFFERTIME = 4 # time to wait before playing
MAX_BUFFER = 30 # the maximum amount of buffer allowed
MAXRETRIES = 2
PAUSE_BETWEEN_SEGMENTS = 1

PLAYBACK_INFO_KEY = "playback_info"
M3U8_MANIFEST_URL_KEY = "m3u8_url_template"
REPLACES_X_WITH_Y = ("$encryption_type$", "internal")

BANDWIDTH_KEY = "bandwidth"
CODECS_KEY = "codecs"


class HLSManifest(BaseManifest):
    HLS_NAME = "HLS"
    """
    The playlist that handles parsing a HLS Version 3 Master Manifest
    """


    @property
    def playlist(self):
        try:
            return self._asset_periods[0]
        except IndexError:
            return None


    @property
    def endlist(self):
        try:
            return self.playlist._endlist
        except TypeError:
            return True


    def __init__(self, url, player, quality=0, codecs=[]):
        BaseManifest.__init__(self, HLSManifest.HLS_NAME, url, quality, codecs, player)


    def parse(self,manifest):
        """
        Parses the inital URL into a master manifest
        :param manifest:
        :return:
        """
        media_playlists = []
        lines = manifest.split('\n')

        assert(lines[0].startswith('#EXTM3U'))

        for i,line in enumerate(lines):
            if line.startswith('#EXT-X-STREAM-INF'):
                key,val = line.split(':')
                attr = cast.my_cast(val)
                name = lines[i+1].rstrip() # next line
                bandwidth = attr[BANDWIDTH_KEY]
                codecs = attr[CODECS_KEY][0]
                url = urlparse.urljoin(self._url, name) # construct absolute url
                media_playlists.append(HLSPlaylist(url, bandwidth, codecs, self))
            elif line.startswith('#EXT-X-'):
                try:
                    key,val = line.split(':')
                except ValueError:
                    key = line[:]
                    val = 'YES'
                key = cast.attr_name(key)
                val = cast.my_cast(val)
                setattr(self,key,val)

        self._asset_periods = [self._choose_playlist(media_playlists)]

    def _choose_playlist(self, playlists):
        """
        chooses the playlist based on the wanted codecs and quality
        :param playlists:
        :return:
        """

        playlists.sort(key=lambda x: x._bandwidth, reverse=True)
        if self._codecs:
            for i, playlist in enumerate(playlists):
                for codec in self._codecs:
                    if codec not in playlists._codecs:
                        playlists.pop(i)
        if len(playlists) == 0:
            # in this case we looked for media playlists, but didn't find any.
            # maybe we're looking at a stream that only has a single bitrate
            # and all the fragments are in the master playlist
            if self._codecs:
                raise CodecNotFound("Codecs not found - Codecs requested: {c}, url: {u}".format(c=str(self._codecs),
                                                                                                u=str(self._url)))
            else:
                playlists = [HLSPlaylist(self._url, -1, [], self)]
        try:
            playlist = playlists[self._quality]
        except IndexError:
            playlist = playlists[-1]

        return playlist



class HLSPlaylist(MediaPlaylist):
    """
    The playlist that handles parsing a specified bit-rate within the Master Manifest
    """
    def __init__(self, url, bandwidth, codecs, manifest):
        MediaPlaylist.__init__(self, url, manifest)

        self._media_fragments = []
        self._endlist = False
        self._codecs = codecs
        self._bandwidth = bandwidth
        self._period_sort_key = bandwidth
        self.last_manifest_time = None

    def _request_media_fragment(self):
        current_media_fragment = self.__get_media_fragment(self.current_index)
        success = True
        retries = 0
        resp = current_media_fragment.download()
        while not resp:
            if retries >= MediaPlaylist.SEGMENT_RETRIES:
                success = False
                break
            else:
                resp = current_media_fragment.download()
                retries += 1
        return success


    def parse(self,manifest):
        """
        Parses the segments within the bit-rate manifest so they can be played
        :param manifest:
        :return:
        """
        ms_counter = None
        lines = manifest.split('\n')
        assert(lines[0].startswith('#EXTM3U'))
        for i,line in enumerate(lines):
            if line.startswith('#EXTINF'):
                """
                Format = #EXTINF:Duration,
                         filename.ts
                Ex = #EXTINF:3
                     20110324T100801.tt

                We gather the duration is the attributes section assuminmg its the only attribute

                """
                key,val = line.split(':')
                attr = cast.my_cast(val)
                name = lines[i+1].rstrip() # next line
                if not ms_counter:  #
                    try:
                        ms_counter = self.media_sequence  # probably live
                    except AttributeError:
                        ms_counter = 1  # probably VOD
                if not name.startswith('#'):
                    # TODO, bit of a hack here. Some manifests put an attribute
                    # line on the first fragment which breaks this.
                    if ms_counter > self.__last_media_sequence():
                        if not self._seg_duration:
                            self._seg_duration = attr[0]
                        url = urlparse.urljoin(self._url, name) # construct absolute url
                        self._media_fragments.append(MediaFragment(name,
                                                                  url,
                                                                  self,
                                                                  ms_counter))
                ms_counter += 1
            elif line.startswith('#EXT-X-'):
                try:
                    key,val = line.split(':')
                except ValueError:
                    key = line[:]
                    val = 'YES'
                key = cast.attr_name(key)
                val = cast.my_cast(val)
                if "URI" in line:
                    continue
                else:
                    setattr(self,key,val)
        self._first_seg_index = self.__first_media_sequence()
        self._total_segments = len(self._media_fragments)

    def __first_media_sequence(self):
        """
        retrieves the first segment
        :return:
        """
        try:
            return self._media_fragments[0].media_sequence
        except IndexError:
            return -1

    def __last_media_sequence(self):
        """
        retrieves the last segment
        :return:
        """
        try:
            return self._media_fragments[-1].media_sequence
        except IndexError:
            return -1

    def __get_media_fragment(self, msq):
        """
        retrieves a segment based on an index
        :param msq:
        :return:
        """
        idx = msq - self.__first_media_sequence()
        if self._media_fragments[idx].media_sequence != msq:
            raise MissedFragment('Fragments are not numbered '
                                  'sequentially: {0}!={1}'.format(
                                  self._media_fragments[idx].media_sequence,
                                  msq))
        return self._media_fragments[idx]

class MediaFragment(LocustRequestObject):
    """
    This class represent an actual media segment
    """

    def __init__(self,name,url,parent=None, seq=None):
        LocustRequestObject.__init__(self)
        self.set_as_parent_request_vars(parent)
        self._url = url
        self.name=name
        self._parent = parent
        self.media_sequence = seq

    def download(self):
        """
        actually downloads the segment
        :return:
        """
        name = self._parent.seg_name
        #assert(str(self.media_sequence) in self.name) # HACK
        r = self.request(name=name)
        if r:
            return True
        else:
            return False







class HLSPlayer(BasePlayer):
    PLAYER_TYPE_NAME = "HLS"
    QVT_KEY_SEQUENCE = [PLAYBACK_INFO_KEY, M3U8_MANIFEST_URL_KEY]
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
        BasePlayer.__init__(self, HLSPlayer.PLAYER_TYPE_NAME, HLSPlayer.QVT_KEY_SEQUENCE, HLSPlayer.QVT_REPLACE)
        self._last_manifest_time = None
        self._seg_duration = None




    def _setup(self, url, quality, codecs, player):
        # download and parse master playlist
        hls_manifest = HLSManifest(url, player, quality, codecs)
        hls_manifest.download()
        self._last_manifest_time = time.time()
        self._manifest = hls_manifest





    def did_load_buffer(self):
        try:
            success = self._manifest.download()
        except MissedFragment as e:
            # TODO: what do we do when we miss a media fragment
            events.request_failure.fire(request_type="GET",
                                        name=self._manifest.playlist._url,
                                        response_time=self.time_played,
                                        exception=e)
            return self.total_loaded_buffer, self.time_played
        if not self._manifest.endlist:  # only update manifest on live
            manifest_age = (time.time() - self._last_manifest_time)
            if self._manifest.playlist.targetduration is None:
                print("huh")
            if self.segment_duration is None:
                print("heh")
            if manifest_age > self._manifest.playlist.targetduration * self.segment_duration:  # vlc does this
                self._manifest.playlist.__setup = False
                self._manifest.playlist.download()
                self._last_manifest_time = time.time()
        return success


