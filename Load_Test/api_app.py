from flask import Flask, request, jsonify
from flask_jsonrpc import JSONRPC
from Load_Test import LoadRunnerAPIWrapper
from flask_cors import cross_origin, CORS

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
        return_value = LoadRunnerAPIWrapper.TEST_API_WRAPPER.is_running()
        return return_value

    @jsonrpc.method("isSetup() -> dict")
    def is_setup():
        return LoadRunnerAPIWrapper.TEST_API_WRAPPER.is_setup()

    @jsonrpc.method(
        "setupManualTest(api_call_weight=dict, env=str, node=int, version=int, n_min=int, n_max=int) -> dict",
        validate=True)
    def setup_manual_test(api_call_weight, env, node, version, n_min, n_max):

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

    @jsonrpc.method("shutdown()")
    def shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


    @app.route('/test', methods=["POST"])
    def test():
        data = request.get_data()
        print(data)

    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'

        if request.method == 'OPTIONS':
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            headers = request.headers.get('Access-Control-Request-Headers')
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Max-Age"] = 86400
            if headers:
                response.headers['Access-Control-Allow-Headers'] = headers

        return response

    app.after_request(add_cors_headers)

    app.run(**kwargs)
