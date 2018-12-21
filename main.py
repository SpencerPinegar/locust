from flask import Flask, request
from flask_jsonrpc import JSONRPC
from app.Core.load_runner import LoadRunner
from app.Data.config import Config
from app.Utils.utils import force_route_version_to_ints
from setproctitle import setproctitle
import os

os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY', 'YES')
os.environ['no_proxy'] = '*'
config = Config()
setproctitle(config.program_name)
app = Flask(__name__)
jsonrpc = JSONRPC(app, config.rpc_endpoint, enable_web_browsable_api=True)
LoadRunner.setup(config, True)


########################################################################################################################
########################################## Server Funcs  ##############################################################
########################################################################################################################

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


########################################################################################################################
##########################################  Undistributed Funcs  ##############################################################
########################################################################################################################

@jsonrpc.method("startCustomRecAPITest(api_call_weight=dict, env=str, node=int, max_request=bool, num_users=int, "
                "hatch_rate=float, stat_interval=int, assume_tcp=bool, bin_by_resp=bool) -> dict")
def start_custom_recapi_test(api_call_weight, env, node, max_request, num_users, hatch_rate, stat_interval=None,
                      assume_tcp=False, bin_by_resp=False):
    api_call_weight = force_route_version_to_ints(api_call_weight)
    LoadRunner.PERSISTANT_LOAD_RUNNER.custom_recapi_test(api_call_weight, env, node, max_request, stat_interval=stat_interval,
                                                         assume_tcp=assume_tcp, bin_by_resp=bin_by_resp)

    LoadRunner.PERSISTANT_LOAD_RUNNER.start_ramp_up(num_users, hatch_rate, first_start=True)
    return LoadRunner.PERSISTANT_LOAD_RUNNER.is_running()

@jsonrpc.method("startCustomMetaDataTest(action=str, put_size=int, total_assets=int, env=str, node=int, stat_int=int,"
                "num_users=int, hatch_rate=float) -> dict")
def start_custom_metadata_test(action, put_size, total_assets, env, node, stat_int, num_users, hatch_rate):
        LoadRunner.PERSISTANT_LOAD_RUNNER.custom_metadata_test(action, put_size, total_assets, env, node, stat_int)
        LoadRunner.PERSISTANT_LOAD_RUNNER.start_ramp_up(num_users, hatch_rate)


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


def run_app():
    app.run(host=config.preferred_master, port=config.rpc_port)

if __name__ == "__main__":
   run_app()
