from flask import Flask, request
from flask_jsonrpc import JSONRPC
from API_Load_Test.load_runner_api_wrapper import LoadRunnerAPIWrapper
from API_Load_Test.load_runner import LoadRunner
from API_Load_Test.Config.config import Config


# TODO: make Initial LoadRunner Variables come from config file
#TODO: make api extension come from config file
extension = '/LoadServer'
app = Flask(__name__)
jsonrpc = JSONRPC(app, extension, enable_web_browsable_api=True)
config = Config()
load_runner = LoadRunner(LoadRunnerAPIWrapper.master_host_info, LoadRunnerAPIWrapper.web_ui_host_info,
                         LoadRunnerAPIWrapper.Slave_Locust_File, LoadRunnerAPIWrapper.Master_Locust_File, config)
test_api_wrapper = LoadRunnerAPIWrapper(config, LoadRunnerAPIWrapper)



@jsonrpc.method("stop_test() -> dict")
def kill():
    test_api_wrapper.stop_tests()
    return test_api_wrapper.is_running()


@jsonrpc.method("ping() -> str")
def ping():
    return u"alive"


@jsonrpc.method("isTestRunning() -> dict")
def is_test_running():
    return test_api_wrapper.is_running()



@jsonrpc.method("startManuelTest(api_call_weight=dict, env=str, node=int, version=int, n_min=int, n_max=int) -> str", validate=True)
def start_manuel_test(api_call_weight, env, node, version, n_min, n_max):
    test_api_wrapper.start_manuel_test(api_call_weight, env, node, version, n_min, n_max)
    return test_api_wrapper.is_setup()

@jsonrpc.method("startBenchmarkTest(api_call_weight=dict, env=str, node=int, version=int, n_min=int, n_max=int,"
                "num_clients=int, hatch_rate=float, run_time=str, reset_stats=bool) -> str", validate=True)
def start_benchmark_test(api_call_weight, env, node, version, n_min, n_max, num_clients, hatch_rate, run_time, reset_stats):
    test_api_wrapper.start_benchmark_test(api_call_weight, env, node, version, n_min, n_max, num_clients, hatch_rate,
                                          run_time, reset_stats)
    return test_api_wrapper.is_setup()



def start_app():
    app.run(host=LoadRunnerAPIWrapper.web_api_host_info[0], port=LoadRunnerAPIWrapper.web_api_host_info[1])

def shutdown_app():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()