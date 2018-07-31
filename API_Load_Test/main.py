from API_Load_Test.load_runner import LoadRunner

from flask import Flask
import os

API_LOAD_TEST_DIR = os.path.pardir(os.path.abspath(__file__))

MASTER_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "master_locust.py")
SLAVE_LOCUST_FILE = os.path.join(API_LOAD_TEST_DIR, "api_locust.py")
master_host_info = ("127.0.0.1", 5557)
web_ui_host_info = ("localhost", 8089)


#TODO: make Initial LoadRunner Variables come from config file
load_runner = LoadRunner(master_host_info, web_ui_host_info, SLAVE_LOCUST_FILE, MASTER_LOCUST_FILE)
app = Flask(__name__)


@app.route('/isTestRunning/', methods=["GET"])
def is_test_running():
    return load_runner.is_test_currently_running()


@app.route("/startTest")
def start_test()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
