from API_Load_Test.api_app import app
from API_Load_Test.load_runner_api_wrapper import TestAPIWrapper





if __name__ == "__main__":
    app.run(host=TestAPIWrapper.web_api_host_info[0], port=TestAPIWrapper.web_api_host_info[1])
