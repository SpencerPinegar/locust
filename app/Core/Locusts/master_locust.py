import logging
from locust import TaskSet, HttpLocust
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)
logger.info("IMPORTED WEB UI SUCCESFULLY")
logging.disable(logging.CRITICAL)

class EmptyTaskSet(TaskSet):
    pass

class MasterUser(HttpLocust):
    min_wait = 0
    max_wait = 0
    task_set = EmptyTaskSet




