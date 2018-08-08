from flask import Flask, request
from flask_jsonrpc import JSONRPC
from Load_Test import LoadRunnerAPIWrapper


from Load_Test.exceptions import NeedExtensionArgument


# TODO: make Initial LoadRunner Variables come from config file
# TODO: make api extension come from config file
# TODO make object to hold app so I can configure details


def thread_webAPP(extension, **kwargs):
    app = Flask(__name__)
    jsonrpc = JSONRPC(app, extension, enable_web_browsable_api=True)

    @jsonrpc.method("stopTest() -> dict")
    def stop_test():
        LoadRunnerAPIWrapper.TEST_API_WRAPPER.stop_tests()
        return LoadRunnerAPIWrapper.TEST_API_WRAPPER.is_running()

    @jsonrpc.method("ping() -> str")
    def ping():
        return u"alive"

    @jsonrpc.method("isRunning() -> dict")
    def is_running():
        return LoadRunnerAPIWrapper.TEST_API_WRAPPER.is_running()

    @jsonrpc.method("isSetup() -> dict")
    def is_setup():
        return LoadRunnerAPIWrapper.TEST_API_WRAPPER.is_setup()

    @jsonrpc.method(
        "setupManuelTest(api_call_weight=dict, env=str, node=int, version=int, n_min=int, n_max=int) -> dict",
        validate=True)
    def setup_manuel_test(api_call_weight, env, node, version, n_min, n_max):
        LoadRunnerAPIWrapper.TEST_API_WRAPPER.setup_manuel_test(api_call_weight, env, node, version, n_min, n_max)
        return LoadRunnerAPIWrapper.TEST_API_WRAPPER.is_setup()

    @jsonrpc.method("startManuelTest(num_users=int, hatch_rate=float) -> dict")
    def start_manuel_test(num_users, hatch_rate):
        LoadRunnerAPIWrapper.TEST_API_WRAPPER.start_manuel_from_ui(num_users, hatch_rate)
        return LoadRunnerAPIWrapper.TEST_API_WRAPPER.is_running()

    @jsonrpc.method("startBenchmarkTest(api_call_weight=dict, env=str, node=int, version=int, n_min=int, n_max=int,"
                    "num_clients=int, hatch_rate=float, run_time=str, reset_stats=bool) -> dict", validate=True)
    def start_benchmark_test(api_call_weight, env, node, version, n_min, n_max, num_clients, hatch_rate, run_time,
                             reset_stats):
        LoadRunnerAPIWrapper.TEST_API_WRAPPER.setup_and_start_benchmark_test(api_call_weight, env, node, version, n_min,
                                                                             n_max, num_clients, hatch_rate,
                                                                             run_time, reset_stats)
        return LoadRunnerAPIWrapper.TEST_API_WRAPPER.is_running()

    # @jsonrpc.method("shutdown()")
    # def shutdown_server():
    #     func = request.environ.get('werkzeug.server.shutdown')
    #     if func is None:
    #         raise RuntimeError('Not running with the Werkzeug Server')
    #     func()

    app.run(**kwargs)
