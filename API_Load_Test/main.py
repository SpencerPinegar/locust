from API_Load_Test.load_runner import LoadRunner

from flask import Flask
from flask import
import os
from API_Load_Test.Config.config import Config

API_LOAD_TEST_DIR = os.path.pardir(os.path.abspath(__file__))

MASTER_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "master_locust.py")
SLAVE_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "api_locust.py")
master_host_info = ("127.0.0.1", 5557)
web_ui_host_info = ("localhost", 8089)
test_runner_communication_info = ("127.0.0.1", 8000)


#TODO: make Initial LoadRunner Variables come from config file
config = Config()
load_runner = LoadRunner(master_host_info, web_ui_host_info, SLAVE_LOCUST_FILE, MASTER_LOCUST_FILE, config)
app = Flask(__name__)


@app.route('/isTestRunning/', methods=["GET"])
def is_test_running():
    return load_runner.test_currently_running()



#TODO FINISH SIMPLE API
@app.route("/startTest")
def start_test():
    test_already_running = load_runner.test_currently_running()
    if test_already_running and load_runner.no_web is True:
        test_type = "Benchmark"
    elif test_already_running:
        test_type = "online"
    else:
        test_type = "None"

    start_test_status = None

    if test_already_running:
        start_test_status = "Previouse Test Still Running, Try Again Later"
    else:
        try:
    if not test_already_running:

    {"Test Already Running": ,
     }

    #TODO MAKE THIS START THE TEST AND RETURN JSON WITH INFO
    pass



def verify_params(config, params):
    config.api_routes

if __name__ == "__main__":
    app.run(host=test_runner_communication_info[0], port=test_runner_communication_info[1])
