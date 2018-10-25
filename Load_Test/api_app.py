from flask import Flask, request, jsonify
from flask_jsonrpc import JSONRPC
from Load_Test.load_runner_api_wrapper import LoadRunnerAPIWrapper
from flask_cors import cross_origin, CORS
from Load_Test.Misc.utils import force_route_version_to_ints
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



    @jsonrpc.method("startCustomTest(api_call_weight=dict, env=str, node=int, max_request=bool, num_users=int, "
                    "hatch_rate=float, stat_interval=int, assume_tcp=bool, bin_by_resp=bool) -> dict")
    def start_custom_test(api_call_weight, env, node, max_request, num_users, hatch_rate, stat_interval=None,
                          assume_tcp=False, bin_by_resp=False):
        api_call_weight = force_route_version_to_ints(api_call_weight)
        LoadRunnerAPIWrapper.TEST_API_WRAPPER.custom_api_test(api_call_weight, env, node, max_request, stat_interval=stat_interval,
                                                              assume_tcp=assume_tcp, bin_by_resp=bin_by_resp)

        LoadRunnerAPIWrapper.TEST_API_WRAPPER.start_ramp_up(num_users, hatch_rate, first_start=True)
        return LoadRunnerAPIWrapper.TEST_API_WRAPPER.is_running()


    @jsonrpc.method("startAutomatedTest(setup_name=str, procedure_name=str) -> dict", validate=True)
    def start_automated_test(setup_name, procedure_name):
        LoadRunnerAPIWrapper.TEST_API_WRAPPER.run_automated_test_case(setup_name, procedure_name)
        LoadRunnerAPIWrapper.TEST_API_WRAPPER.automated_test.run()
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
