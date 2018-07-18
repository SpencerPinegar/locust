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
