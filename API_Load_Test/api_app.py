from flask import Flask
from flask_jsonrpc import JSONRPC
from API_Load_Test.load_runner_api_wrapper import TestAPIWrapper
# TODO: make Initial LoadRunner Variables come from config file

app = Flask(__name__)
jsonrpc = JSONRPC(app, '/LoadServer', enable_web_browsable_api=True)
test_api_wrapper = TestAPIWrapper()




@jsonrpc.method('App.argsValidateJSONMode(a1=Number, a2=String, a3=Boolean, a4=Array, a5=Object) -> Object',
                validate=True)
def args_validate_json_mode(a1, a2, a3, a4, a5):
    return u'Number: {0}, String: {1}, Boolean: {2}, Array: {3}, Object: {4}'.format(a1, a2, a3, a4, a5)


@jsonrpc.method('App.argsValidatePythonMode(a1=int, a2=str, a3=bool, a4=list, a5=dict) -> object')
def args_validate_python_mode(a1, a2, a3, a4, a5):
    return u'int: {0}, str: {1}, bool: {2}, list: {3}, dict: {4}'.format(a1, a2, a3, a4, a5)


@jsonrpc.method("ping")
def ping():
    return u"alive"


@jsonrpc.method("isTestRunning() -> dict")
def is_test_running():
    return test_api_wrapper.is_test_running()



@jsonrpc.method("startManuelTest(api_call_weight=dict, env=str, node=int, version=int, n_min=int, n_max=int) -> str", validate=True)
def start_manuel_test(api_call_weight, env, node, version, n_min, n_max):
    test_api_wrapper.start_manuel_test(api_call_weight, env, node, version, n_min, n_max)
    return test_api_wrapper.verify_started()

@jsonrpc.method("startBenchmarkTest(api_call_weight=dict, env=str, node=int, version=int, n_min=int, n_max=int,"
                "num_clients=int, hatch_rate=float, run_time=str, reset_stats=bool) -> str", validate=True)
def start_benchmark_test(api_call_weight, env, node, version, n_min, n_max, num_clients, hatch_rate, run_time, reset_stats):
    test_api_wrapper.start_benchmark_test(api_call_weight, env, node, version, n_min, n_max, num_clients, hatch_rate,
                                          run_time, reset_stats)
    return test_api_wrapper.verify_started()