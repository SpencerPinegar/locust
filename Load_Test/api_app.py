from flask import Flask
from flask_jsonrpc import JSONRPC
from Load_Test.load_runner_api_wrapper import LoadRunnerAPIWrapper
from Load_Test.load_runner import LoadRunner
from Load_Test.Config.config import Config


# TODO: make Initial LoadRunner Variables come from config file
#TODO: make api extension come from config file
#TODO make object to hold app so I can configure details
extension = '/LoadServer'
app = Flask(__name__)
jsonrpc = JSONRPC(app, extension, enable_web_browsable_api=True)
config = Config()
load_runner = LoadRunner(LoadRunnerAPIWrapper.master_host_info, LoadRunnerAPIWrapper.web_ui_host_info,
                         LoadRunnerAPIWrapper.Slave_Locust_File, LoadRunnerAPIWrapper.Master_Locust_File, config)
load_runner.default_2_cores = True
test_api_wrapper = LoadRunnerAPIWrapper(config, load_runner)



@jsonrpc.method("stopTest() -> dict")
def stop_test():
    test_api_wrapper.stop_tests()
    return test_api_wrapper.is_running()


@jsonrpc.method("ping() -> str")
def ping():
    return u"alive"


@jsonrpc.method("isRunning() -> dict")
def is_running():
    return test_api_wrapper.is_running()


@jsonrpc.method("isSetup() -> dict")
def is_setup():
    return test_api_wrapper.is_setup()


@jsonrpc.method("setupManuelTest(api_call_weight=dict, env=str, node=int, version=int, n_min=int, n_max=int) -> dict", validate=True)
def setup_manuel_test(api_call_weight, env, node, version, n_min, n_max):
    test_api_wrapper.setup_manuel_test(api_call_weight, env, node, version, n_min, n_max)
    return test_api_wrapper.is_setup()


@jsonrpc.method("startManuelTest(num_users=int, hatch_rate=float) -> dict")
def start_manuel_test(num_users, hatch_rate):
    test_api_wrapper.start_manuel_from_ui(num_users, hatch_rate)
    return test_api_wrapper.is_running()


@jsonrpc.method("startBenchmarkTest(api_call_weight=dict, env=str, node=int, version=int, n_min=int, n_max=int,"
                "num_clients=int, hatch_rate=float, run_time=str, reset_stats=bool) -> dict", validate=True)
def start_benchmark_test(api_call_weight, env, node, version, n_min, n_max, num_clients, hatch_rate, run_time, reset_stats):
    test_api_wrapper.setup_and_start_benchmark_test(api_call_weight, env, node, version, n_min, n_max, num_clients, hatch_rate,
                                                    run_time, reset_stats)
    return test_api_wrapper.is_running()


