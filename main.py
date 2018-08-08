
from Load_Test.api_app import thread_webAPP
from Load_Test import LoadRunnerAPIWrapper
from Load_Test.graceful_killer import GracefulKiller
import time
import threading




def main_func(two_cores):
    LoadRunnerAPIWrapper.setup()
    LoadRunnerAPIWrapper.TEST_API_WRAPPER.default_2_cores = two_cores
    LoadRunnerAPIWrapper.TEST_API_WRAPPER._test_runner._default_2_cores = two_cores
    killer = GracefulKiller()
    app_args = {
        "port": LoadRunnerAPIWrapper.web_api_host_info[1],
        "host": LoadRunnerAPIWrapper.web_api_host_info[0]
    }
    t_webApp = threading.Thread(name='Web App', target=thread_webAPP, args=(LoadRunnerAPIWrapper.Extension,), kwargs=app_args)
    t_webApp.setDaemon(True)
    t_webApp.start()


    while True:
        time.sleep(1)
        if killer.kill_now:
            LoadRunnerAPIWrapper.teardown()
            print("exiting")
            exit(0)


if __name__ == "__main__":
    main_func(False)








