__version__ = "0.8.1"

from .core import HttpLocust, Locust, TaskSet, task
from .core import HttpLocust, Locust, TaskSet, TaskSequence, task, seq_task
from .exception import InterruptTaskSet, ResponseError, RescheduleTaskImmediately
from .main import run_locust, create_options, parse_options

