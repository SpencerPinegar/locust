
from Load_Test.api_app import thread_webAPP
from Load_Test.load_runner import LoadRunner
from Load_Test.Misc.graceful_killer import GracefulKiller
from Load_Test.load_server_client import LoadServerClient
import time
import threading
from requests.exceptions import ConnectionError
import os



def shutdown(host):
    try:
        client = LoadServerClient(host, LoadRunner.Extension)
        client.shutdown()
    except ConnectionError:
        return




def main_func(two_cores, host):
    os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY', 'YES')
    os.environ['no_proxy'] = '127.0.0.1,localhost,0.0.0.0'
    killer = GracefulKiller()
    app_args = {
        "port": LoadRunner.web_api_host_info[1],
        "host": LoadRunner.web_api_host_info[0]
    }
    t_webApp = threading.Thread(name='Web App', target=thread_webAPP, args=(LoadRunner.Extension, two_cores,),
                                kwargs=app_args)
    t_webApp.setDaemon(True)
    t_webApp.start()


    while True:
        time.sleep(1)
        if killer.kill_now:
            shutdown(host)
            print("exiting")
            exit(0)


if __name__ == "__main__":
    main_func(False, LoadServerClient.lgen8_host_name)








