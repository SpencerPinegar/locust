from collections import namedtuple
from app.Data.sql_route_statements import TEST_SQL_STATEMENTS
import random
import hashlib
import re
import subprocess32 as sp
import os
import socket

size_key ="size"
element_lb_key = "norm_lower"
element_ub_key = "norm_upper"
optional_fields_key = "optional_fields"
weight_key = "weight"


API_VERSION_KEYS = [size_key, element_ub_key, element_ub_key, optional_fields_key, weight_key]


def merge_dicts(dict1, dict2):
    for key, value in dict2.items():
        dict1[key] = value
    return dict1


def execute_select_statement(config, query_or_route_name, env):
    if "select" not in query_or_route_name.lower():
        query_or_route_name = TEST_SQL_STATEMENTS[query_or_route_name]
    conn = config.get_db_connection(env)
    try:
        with conn.cursor() as cur:
            cur.execute(query_or_route_name)
            data = cur.fetchall()
            return data
    except Exception as e:
        raise e
    finally:
        conn.close()


def execute_commit_statement(config, query, env):
    conn = config.get_db_connection(env)
    try:
        with conn.cursor() as cur:
            count = cur.execute(query)
            conn.commit()
            return count
    except Exception as e:
        raise e
    finally:
        conn.close()

def clean_stdout(txt):
    try:
        return re.sub(r'[\[].*?(?<=[\]]) [^:]*: ', '', txt)
    except TypeError:
        return txt

def compute_short_hash(txt, length=6):
    # This is just a hash for debugging purposes.
    #    It does not need to be unique, just fast and short.
    hash = hashlib.sha1()
    hash.update(txt)
    return hash.hexdigest()[:length]

def get_api_info(version_params):
    weight = version_params[weight_key]
    size = version_params[size_key]
    element_size_lb = version_params[element_lb_key]
    element_size_up = version_params[element_ub_key]
    optional_fields = version_params[optional_fields_key]
    CallInfo = namedtuple("CallInfo", ["weight", "size", "element_lb", "element_ub", "optional_fields"])
    return CallInfo(weight, size, element_size_lb, element_size_up, optional_fields)

def build_api_info(weight, size, element_size_lb, element_size_ub, optional_fields=None):
    api_info = {}
    api_info[size_key] = size
    api_info[weight_key] = weight
    api_info[element_lb_key] = element_size_lb
    api_info[element_ub_key] = element_size_ub
    api_info[optional_fields_key] = optional_fields if optional_fields is not None else {}
    return api_info



def obtain_version_number_based_on_weight_func(api_weight):
    VersionWeight = namedtuple("VersionWeight", ["version", "weight"])
    version_weight = []
    total_weight = 0
    print(api_weight)
    for version, version_info in api_weight.items():
        weight = get_api_info(version_info).weight
        version_weight.append(VersionWeight(version, weight))
        total_weight += weight

    def version_based_on_weight(*args):
        value_num = random.randint(0, total_weight - 1)
        running_count = 0
        for vers_weight in version_weight:
            running_count += vers_weight.weight
            if value_num < running_count:
                return vers_weight.version

    return version_based_on_weight


def force_route_version_to_ints(api_route):
    for route, route_params in api_route.items():
        to_be_route_params = {}
        for version, version_params in route_params.items():
            try:
                to_be_route_params[int(version)] = version_params
            except ValueError: #All routes have been validated prior, if the route isnt then it is a handled exception
                to_be_route_params[version] = version_params
                continue
        api_route[route] = to_be_route_params
    return api_route

def to_sized_hex(number_to_hex, size_of_hex):
    formatter = "0x%0" + str(size_of_hex) + "x"
    number =  formatter % number_to_hex
    return number[2:]

def start_hosts(hosts, program_name):
    cmd = get_python_path() + " " + get_entrance_path()
    for host in hosts:
        # Ports are handled in ~/.ssh/config since we use OpenSSH
        COMMAND = "pgrep -x {0}".format(program_name)

        ssh = sp.Popen(["ssh", "%s" % host, COMMAND],
                               shell=True,
                               stdout=sp.PIPE,
                               stderr=sp.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            error = ssh.stderr.readlines()
            print( "ERROR: %s" % error)
        else:
            print (result)


def get_performance_test_dir():
    performance_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return performance_dir

def get_entrance_path():
    if on_lgen_server():
        return "/home/spinegar/Performance_Test/main.py"
    return os.path.join(get_performance_test_dir(), "main.py")


def get_python_path():
    if on_lgen_server():
        return "/home/spinegar/Performance_Test/localVenv/bin/python"
    return "/Users/spencerpinegar/PycharmProjects/Performance_Test/venv/bin/python"

def on_lgen_server():
    return "lgen" in socket.getfqdn()

