

class CMSTimeOut(Exception):
    """
    This Exception is returned when a response took longer than the max time
    """
    pass


class Non200ResponseCodeException(Exception):
    """
    This Exception is return when a response does not return a response code
    """
    pass


class LoadRunnerFailedClose(Exception):
    """
    This Exception is return when the Load Runner does not properly close
    """
    pass

class TestAlreadyRunning(Exception):
    """
    This Exception is raised when the server is told to start a test and the test is already running
    """
    pass

class InvalidPlaybackRoute(Exception):
    """
    This Exception is raised when the server is told to load test an invalid Playback Route
    """
    pass
class InvalidPlaybackPlayer(Exception):
    """
    This Exception is raised when the server is told to load test with an invalid Player
    """
    pass
class InvalidCodec(Exception):
    """
    This Exception is raised when the codec isn't a list of strings
    """
    pass

class InvalidRoute(Exception):
    """
    This Exception is raised when the server is told to load test an invalid API Route
    """
    pass

class InvalidAPIEnv(Exception):
    """
    This Exception is raised when the server is told to load test an invalid API Env
    """
    pass

class InvalidAPINode(Exception):
    """
    This Exception is raised when the server is told to load test an invalid API Node
    """
    pass

class InvalidAPIVersion(Exception):
    """
    This Exception is raised when the server is told to load test an invalid API Version
    """
    pass

class OptionTypeError(Exception):
    """
    This Exceptions is raised when a option is an invalid type
    """

class LocustUIUnaccessible(Exception):
    """
    This Exception is raised when the server can't access the Locust website when it is running a Load Test
    """
    pass

class SlaveInitilizationException(Exception):
    """
    This Exception is raised when the an incorrect number of slave locusts are created
    """
    pass

class FailedToStartLocustUI(Exception):
    """
    This Exception is raised when the Locust UI can not be accessed
    """
    pass

class AttemptAccessUIWhenNoWeb(Exception):
    """
    This Exception is raised when someone attempts to access the Locust UI while no web is on
    """
    pass

class NotEnoughAvailableCores(Exception):
    """
    This Exception is raised when someone attempts to run multi-core locust on a machine without enough available cores
    """
    pass

class LostTestRunnerAPIObject(Exception):
    """
    This Exception is raised when someone attempts to teardown a testAPIWrapper and it cannot be found
    """
    pass

class NeedExtensionArgument(Exception):
    """
    This Exception is raised when someone attempts to start a flask webapp without an extension
    """
    pass

class WebOperationNoWebTest(Exception):
    """
    This Exception is raised when someone attempts to interact with the UI on no web test
    """
    pass

class InvalidAPIVersionParams(Exception):
    """
    This Exception is raised when someone attempts run a route version without supplying necessary api keys
    """
    pass

class InvalidPlayerType(Exception):
    """
    This Exception is raised when someone attempts to run a playback test on an unsupported player
    """
    pass

class InvalidPlaybackRoute(Exception):
    """
    This Exception is raised when someone attempts to run a playback test with an unsupported route
    """
    pass



##########################################PLAYBACK EXCEPTIONS############################################
class BufferUnderrun(Exception):
    """
    Thrown when the playeris waiting for buffer
    """
    pass

class StaleManifest(Exception):
    """
    Thrown when the Manifest doesnt have needed information
    """
    pass

class StalePlaylist(Exception):
    """
    Thrown when the Playlist doesn't have needed information
    """

class ManifestDownloadBeforeSetup(Exception):
    """
    Thrown when a Dash manifest is downloaded before it is setup
    """
    pass


class MissedFragment(Exception):
    """
    Thrown when a Segment isn't found
    """
    pass

class BadContentLength(Exception):
    """
    Thrown when the segment header for content length doesnt match the length of the content
    """
    pass

class QVTRequestException(Exception):
    """
    Thrown when the QVT is not returned correctly
    """
    pass
class MissingProfilesException(Exception):
    """
    Thrown when the manifest retreived doesn't have any stream information
    """
    pass
class CodecNotFound(Exception):
    """
    Thrown when a Dash manifest cannot find a video adaptation set with the given codec
    """
    pass
class QMXPlaylistNoStreams(Exception):
    """
    Thrown when a playlist doesn't have any streams
    """
    pass

class HLSPlaylist(Exception):
    """
    Thrown when a HLS player cannot load its selected playlist url
    """

class DashManifestInitialURL(Exception):
    """
    Thrown when the Dash manifest Initial URL can not be loaded
    """
    pass

class DashManifestMissingPeriods(Exception):
    """
    Thrown when the Dash manifest does not have any periods
    """
    pass

class DashNodeAttributeKeyError(Exception):
    """
    Thrown when a Dash node from the manifest does not have the expected keys
    """
    pass

class DashPeriodMissingAdaptationSet(Exception):
    """
    Thrown when a Dash Period does not have any adaptation sets
    """
    pass

class DashPeriodMissingBaseURL(Exception):
    """
    Thrown when a Dash Period does not have a base url
    """
    pass

class DashMissingSegmentTemplate(Exception):
    """
    Thrown when a Dash Adaptation Set does not contain  Segment Template child
    """
    pass

class DashMissingRepresentations(Exception):
    """
    Thrown when a Dash Adaptation Set does not contain any Representations
    """
    pass

class DashTimeParseIssue(Exception):
    """
    Thrown when a Dash manifest cannot parse a time string recieved from XML to integers
    """
    pass


class DashManifestPeriodSetup(Exception):
    """
    Thrown when a Dash Period cannot setup
    """
    pass
class DashManifestPeriodSegmentPull(Exception):
    """
    Thrown when a Segment could not be pulled
    """
    pass

