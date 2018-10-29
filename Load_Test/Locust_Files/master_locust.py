print("entered master locust")
import os
# def set_virtual_env():
#     PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     LOCALVENV_DIR = os.path.join(PROJECT_DIR, "localVenv/")
#     VENV_DIR = os.path.join(PROJECT_DIR, "venv/")
#     activate_virtual_env_path = "bin/activate_this.py"
#     if os.path.isdir(LOCALVENV_DIR):
#         path = os.path.join(LOCALVENV_DIR, activate_virtual_env_path)
#         execfile(path, dict(__file__=path))
#     elif os.path.isdir(VENV_DIR):
#         path = os.path.join(VENV_DIR, activate_virtual_env_path)
#         execfile(path, dict(__file__=path))
#     else:
#         raise Exception("Could not find virutal env")
# #set_virtual_env()

from locust import TaskSet, HttpLocust
from setproctitle import setproctitle

setproctitle("-LOCUST WEB UI MASTER")
print("IMPORTED SUCCESFULLY")
class EmptyTaskSet(TaskSet):
    pass

class MasterUser(HttpLocust):
    min_wait = 0
    max_wait = 0
    task_set = EmptyTaskSet




