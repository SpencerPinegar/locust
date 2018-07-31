

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
