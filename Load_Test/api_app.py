



# TODO: make Initial LoadRunner Variables come from config file
# TODO: make api extension come from config file
# TODO make object to hold app so I can configure details


def thread_webAPP(extension, two_cores, **kwargs):
    from flask import Flask, request
    from flask_jsonrpc import JSONRPC
    from Load_Test.load_runner import LoadRunner
    from Load_Test.Data.config import Config
    from Load_Test.Misc.utils import force_route_version_to_ints
    app = Flask(__name__)
    jsonrpc = JSONRPC(app, extension, enable_web_browsable_api=True)
    LoadRunner.setup(Config(), two_cores)



    @jsonrpc.method("stopTest() -> dict")
    def stop_test():
        LoadRunner.PERSISTANT_LOAD_RUNNER.stop_tests()
        return LoadRunner.PERSISTANT_LOAD_RUNNER.is_running()

    @jsonrpc.method("ping() -> str")
    def ping():
        return u"alive"

    @jsonrpc.method("isRunning() -> dict")
    def is_running():
        return_value = LoadRunner.PERSISTANT_LOAD_RUNNER.is_running()
        return return_value



    @jsonrpc.method("startCustomAPITest(api_call_weight=dict, env=str, node=int, max_request=bool, num_users=int, "
                    "hatch_rate=float, stat_interval=int, assume_tcp=bool, bin_by_resp=bool) -> dict")
    def start_custom_api_test(api_call_weight, env, node, max_request, num_users, hatch_rate, stat_interval=None,
                          assume_tcp=False, bin_by_resp=False):
        api_call_weight = force_route_version_to_ints(api_call_weight)
        LoadRunner.PERSISTANT_LOAD_RUNNER.custom_api_test(api_call_weight, env, node, max_request, stat_interval=stat_interval,
                                                              assume_tcp=assume_tcp, bin_by_resp=bin_by_resp)

        LoadRunner.PERSISTANT_LOAD_RUNNER.start_ramp_up(num_users, hatch_rate, first_start=True)
        return LoadRunner.PERSISTANT_LOAD_RUNNER.is_running()

    @jsonrpc.method("startCustomPlaybackTest(client=str, playback_test=str, quality=int, codecs=list,"
                    "users=int, hatch_rate=float, dvr=int, days_old=int, stat_int=int) -> dict")
    def start_custom_playback_test(client, playback_test, quality, codecs, users, hatch_rate, dvr, days_old, stat_int):
        LoadRunner.PERSISTANT_LOAD_RUNNER.custom_playback_test(client, playback_test, quality, codecs, users, dvr, days_old, stat_int)
        LoadRunner.PERSISTANT_LOAD_RUNNER.start_ramp_up(users, hatch_rate)
        return LoadRunner.PERSISTANT_LOAD_RUNNER.is_running()

    @jsonrpc.method("startAutomatedTest(setup_name=str, procedure_name=str) -> dict", validate=True)
    def start_automated_test(setup_name, procedure_name):
        LoadRunner.PERSISTANT_LOAD_RUNNER.run_automated_test_case(setup_name, procedure_name)
        LoadRunner.PERSISTANT_LOAD_RUNNER.automated_test.run()
        return LoadRunner.PERSISTANT_LOAD_RUNNER.is_running()

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
