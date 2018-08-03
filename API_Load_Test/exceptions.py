

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

class InvalidAPIRoute(Exception):
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
