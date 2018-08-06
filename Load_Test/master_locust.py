from locust import TaskSet, HttpLocust


class EmptyTaskSet(TaskSet):
    pass

class MasterUser(HttpLocust):
    min_wait = 0
    max_wait = 0
    task_set = EmptyTaskSet




