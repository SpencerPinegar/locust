from locust import TaskSet, HttpLocust
#from setproctitle import setproctitle

#setproctitle("-LOCUST WEB UI MASTER")

class EmptyTaskSet(TaskSet):
    pass

class MasterUser(HttpLocust):
    min_wait = 0
    max_wait = 0
    task_set = EmptyTaskSet




