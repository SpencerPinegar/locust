import logging
import random
import sys
import requests
import hashlib
import json

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger(__name__)


class RequestPoolFactory:
    """
    Read-Only API's - These API's are functional and do not require a state change - they are simply called with real data

        - User Recordings
        - User Franchise
        - List Rules
        - Mark Watched

    Two-State API's - These API's must change a field in a database row to work, So we grab data in the assumed state,
                           change it to the First state, then revert it to the last state so no real changes are made

        - Protect Recordings
            Assumed State ~ protected = True
            First state ~ protected = False
            Last state ~ protected = True

        - Update Recording Rules
            Assumed State ~ mode = 1 (all)
            First state ~ mode = 2 (new)
            Last state ~ mode = 1 (all)

    Inverse API's - These API's must add/remove a row in a database to work. To accomidate this test users are used
                        created/deleted data is tracked while the test is run ~ at shut down

        - Create/Delete Recordings
        - Create/Delete Recordings Rules
    """

    def __init__(self, config, envs=None):
        self.config = config
        self.env_db_connections = self._init_connections(envs)

    def get_user_recordings_ribbon_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "User Recordings Ribbon"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    def get_user_franchise_ribbon_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "User Franchise Ribbon"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    def get_user_recspace_information_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "User Recspace Information"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    def get_update_user_settngs_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        start_params = {"rs_recspace": 80085}
        end_params = {"rs_recspace": 599}
        route_name = "Update User Settings"
        pool = self._get_two_state_pool(route_name, version, env, start_params, end_params, min_pool_size,
                                        max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    # TODO: CREATE RECORDINGS HERE

    def get_protect_recordings_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        start_params = {"protected": False}
        end_params = {"protected": True}
        route_name = "Protect Recordings"
        pool = self._get_two_state_pool(route_name, version, env, start_params, end_params, min_pool_size,
                                        max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    def get_mark_watched_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "Mark Watched"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    # TODO: DELETE Recordings

    # TODO: Create Rules Here

    def get_update_rules_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        start_params = {"mode": "all"}
        end_params = {"mode": "new"}
        route_name = "Update Rules"
        pool = self._get_two_state_pool(route_name, version, env, start_params, end_params, min_pool_size,
                                        max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route

    # TODO: DELETE RULES HERE

    def get_list_rules_pool_and_route(self, version, env, min_pool_size, max_pool_size, **kwargs):
        route_name = "List Rules"
        pool = self._get_pool(route_name, version, env, min_pool_size, max_pool_size, **kwargs)
        route = self._get_route(route_name, version)
        return pool, route


    def get_redundant_ts_segment_urls(self, env, size, with_known_issue=False, **kwargs):
        route_name = "Redundant Ts Segment"
        return_stream = {}
        prefix = "http://d-gp2-dvrmfs-1123.rd.movetv.com/807b3374758a46418e7eafbb56f3bd28/"
        the_segs = []
        #the_segs = ['1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f94.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f95.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f96.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f97.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f98.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f99.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f9a.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f9b.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f9c.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f9d.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f9e.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006f9f.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa0.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa1.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa2.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa3.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa4.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa5.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa6.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa7.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa8.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fa9.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006faa.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fab.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fac.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fad.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fae.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006faf.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb0.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb1.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb2.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb3.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb4.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb5.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb6.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb7.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb8.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fb9.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fba.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fbb.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fbc.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fbd.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fbe.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fbf.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc0.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc1.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc2.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc3.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc4.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc5.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc6.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc7.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc8.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fc9.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fca.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fcb.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fcc.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fcd.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fce.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fcf.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd0.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd1.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd2.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd3.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd4.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd5.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd6.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd7.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd8.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fd9.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fda.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fdb.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fdc.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fdd.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fde.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fdf.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe0.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe1.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe2.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe3.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe4.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe5.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe6.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe7.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe8.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fe9.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fea.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006feb.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fec.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fed.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fee.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fef.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff0.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff1.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff2.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff3.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff4.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff5.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff6.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff7.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff8.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ff9.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ffa.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ffb.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ffc.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ffd.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006ffe.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500006fff.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007000.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007001.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007002.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007003.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007004.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007005.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007006.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007007.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007008.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007009.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000700a.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000700b.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000700c.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000700d.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000700e.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000700f.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007010.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007011.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007012.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007013.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007014.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007015.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007016.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007017.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007018.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007019.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000701a.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000701b.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000701c.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000701d.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000701e.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000701f.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007020.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007021.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007022.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007023.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007024.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007025.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007026.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007027.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007028.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p0500007029.ts', '1797b780995911e89d940025b5472112/48a78fdce3d411e495fd0a70680a3d78/p050000702a.ts']
        #for index in range(len(the_segs)):
        #    the_segs[index] = prefix + the_segs[index]
        #the_segs.append("http://d-gp2-dvrmfs-1124.rd.movetv.com/be275c33fe5947c494e7e65b3c5e5a89/0c756d68918211e8b9630025b5472210/6c48edbedb6b11e78e3900505697cbbf/p09000025a0.ts")
        #the_segs.append("http://d-gp2-dvrmfs-1123.rd.movetv.com/58de947979af4b81bc31dd243d71e6af/48b31b9e995d11e882500025b5472115/5eac943aba8711e7b74e0a3e7092b342/p0500004b30.ts")
        the_segs.append("http://p-dc10-dvrmfs-2122.rp.movetv.com/a1093a971dd24afd8a75ecc72025910b/a2b88f28919411e8bd4c0025b5472111/5db4cfcedce811e7a824124234136d4e/p0500006740.ts")
        for seg in the_segs:
            ts_request = requests.get(seg)
            if ts_request.status_code != 200:
                assert False is True  #

            ts_hash = hashlib.md5(str(ts_request.content)).hexdigest()
            return_stream.setdefault(seg, ts_hash)
        return list(return_stream.items())

        # if with_known_issue:
        #     ts_hosts = [
        #                "http://d-gp2-dvrmfs-1124.rd.movetv.com/be275c33fe5947c494e7e65b3c5e5a89/0c756d68918211e8b9630025b5472210/6c48edbedb6b11e78e3900505697cbbf/p09000025a0.ts",
        #                 "http://d-gp2-dvrmfs-1123.rd.movetv.com/58de947979af4b81bc31dd243d71e6af/48b31b9e995d11e882500025b5472115/5eac943aba8711e7b74e0a3e7092b342/p0500004b30.ts"
        #                ]
        #     return_stream = {}
        #     for ts_host in ts_hosts:
        #         ts_request = requests.get(ts_host)
        #         if ts_request.status_code != 200:
        #             assert False is True #
        #
        #
        #         ts_hash = hashlib.md5(str(ts_request.content)).hexdigest()
        #         return_stream.setdefault(ts_host, ts_hash)
        #     return list(return_stream.items())
        # else:
        #     conn = self._get_connection(env)
        #     querry = self.config.get_function_querry(route_name)
        #     try:
        #         with conn.cursor() as cur:
        #             cur.execute(querry)
        #             data = cur.fetchall()
        #             self.max_pool_size = len(data)
        #
        #     except Exception as e:
        #         logger.exception(e)
        #         sys.exit(1)
        #     else:
        #         logger.info("Got QVT")
        #         qvt_host = data[0][0]
        #         qvt_response = requests.get(qvt_host)
        #         if qvt_response.status_code != 200:
        #             logger.error("Could not reach QVT Resource {qvt}".format(qvt=qvt_host))
        #         qvt_json = json.loads(qvt_response.content)
        #         m3u8_host = qvt_json[u"playback_info"][u"m3u8_url_template"]
        #         m3u8_host = m3u8_host.replace("$encryption_type$", "internal")
        #         m3u8_resposne = requests.get(m3u8_host)
        #         if m3u8_resposne.status_code != 200:
        #             logger.error("Could not reach M3U8 Resource {M3U8}".format(M3U8=m3u8_host))
        #         m3u8_manifest = m3u8_resposne.content
        #         for line in m3u8_manifest.splitlines():
        #             if line.startswith("#"):
        #                 continue
        #             else:
        #                 #TODO: MAKE IT SO I CAN SELECT BITRATE FROM PARAM
        #                 stream = line
        #                 break
        #
        #         stream_host = m3u8_host.replace("internal_master.m3u8", stream)
        #         stream_response = requests.get(stream_host)
        #         if stream_response.status_code != 200:
        #             logger.error("Could not reach Stream Resource {stream}".format(stream=stream_host))
        #         stream_content = stream_response.content
        #         return_streams = {}
        #         for line in stream_content.splitlines():
        #             if line.startswith("#"):
        #                 continue
        #             elif line.endswith(".ts"):
        #                 ts_host = m3u8_host.replace("internal_master.m3u8", line)
        #                 ts_response = requests.get(ts_host)
        #                 if ts_response.status_code != 200:
        #                     logger.error("Could not reach Ts Segement {ts}".format(ts=ts_host))
        #                 else:
        #                     ts_content = ts_response.content
        #                     ts_hash = hashlib.md5(str(ts_content)).hexdigest()
        #                     return_streams.setdefault(ts_host, ts_hash)
        #                     if len(return_streams) is size:
        #                         return list(return_streams.items())
        #         logger.error("Could Not find enough ts Segments")
    # #
    # TODO: Create Functions To get Create/Delete Request Pools

    def _get_route(self, route, version):
        return self.config.get_api_route(route, version)

    def _get_pool(self, route, version, env, min_pool_size, max_pool_size, **kwargs):

        sql_route, req_fields, opt_fields, min_norm, max_norm, is_list = self._get_route_version_info(route, version)
        datapool = _ReadOnlyRequestPool(sql_route, req_fields, opt_fields, min_norm, max_norm, is_list, min_pool_size,
                                        max_pool_size)
        datapool.init_normal_pool(self._get_connection(env), **kwargs)
        return datapool

    def _get_two_state_pool(self, route, version, env, start_params, end_params, min_pool_size, max_pool_size,
                            **kwargs):
        sql_route, req_fields, opt_fields, min_norm, max_norm, is_list = self._get_route_version_info(route, version)
        datapool = _TwoStateRequestPool(sql_route, req_fields, opt_fields, min_norm, max_norm, start_params, end_params,
                                        is_list, min_pool_size, max_pool_size)
        datapool.init_normal_pool(self._get_connection(env), **kwargs)
        return datapool

    def _init_connections(self, envs):
        connections = {}
        if envs is not None:
            for env in envs:
                connections.setdefault(env, self.config.get_db_connection(env))
            return connections
        else:
            for env in self.config.get_db_environments():
                connections.setdefault(env, self.config.get_db_connection(env))
            return connections

    def _get_connection(self, env):
        return self.env_db_connections[env]

    def _get_route_version_info(self, route, version):
        sql_route, versions_info, min_norm, max_norm, is_list = self.config.get_api_route_specs(route)
        version = versions_info[version]
        req_fields = version["Required Fields"]
        opt_fields = version["Optional Fields"]
        return sql_route, req_fields, opt_fields, min_norm, max_norm, is_list




    def close(self):
        for value in self.env_db_connections.values():
            value.close()

    # TODO:: Create Pool Class for Create/Delete API's; Create-Delete-Recordings, Create-Delete-Recording-Rules


class _ReadOnlyRequestPool(object):

    # TODO:: Make the a method to verify data/responses

    def __init__(self, sql, req_fields, opt_fields, min, max, is_list, min_pool_size, max_pool_size):

        self.is_list = is_list
        self.normal_min = -1 if min == None else min
        self.normal_max = -1 if max == None else max
        self.required_fields = req_fields
        self.optional_fields = opt_fields
        self.max_pool_size = -1
        self.normal_data = True
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._set_SQL(sql)
        self.normal_pool = None




    def add_optional_defualt_params(self, **kwargs):
        for key, value in kwargs.iteritems():
            if not self._is_optional_request_param(key, value):
                logger.error("Invalid default Params")
                return
        for key, value in kwargs.iteritems():
            for item in self.normal_pool:
                item.setdefault(key, value)

    def get_json(self, **kwargs):
        if not self._is_succesful_init():
            logger.error("Random JSON returned is None because no data could be found")
            return

        json = random.choice(self.normal_pool)
        if kwargs is not None:
            return_json = {}
            for key, value in kwargs.iteritems():
                if self._is_optional_request_param(key, value):
                    return_json.setdefault(key, value)
            return_json.update(json)
            return self._listify(return_json)
        else:
            return self._listify(json)

    def init_normal_pool(self, conn, min=-1, max=-1, **kwargs):
        if self.max_pool_size <= 10 and self.max_pool_size != -1:
            logger.debug("Max Pool Size = {0}, There may not be enough normal data to accuratly load test".format(
                self.max_pool_size))
        if min and max == -1:
            min = self.normal_min
            max = self.normal_max
        real_normal_request_data = self._get_normal_request_data(conn, min, max)
        default_dict = {}
        if kwargs is not None:
            for key, value in kwargs.iteritems():
                default_dict.setdefault(key, value)
        real_normal_json_data = self._proccess_normal_request_data(real_normal_request_data, default_dict)
        self.normal_pool = real_normal_json_data

    def _is_succesful_init(self):
        if self.max_pool_size == -1:
            logger.error("normal pool must be initialized prior to getting data")
            return False
        if len(self.normal_pool) < self.min_pool_size:
            logger.error("Your pool was size was {0}: The minimum pool size is {1} - Create more data".format(
                len(self.normal_pool), self.min_pool_size))
            return False
        return True

    def _set_SQL(self, SQL):
        SQL = SQL.lower()
        if self.normal_min and self.normal_max == -1:
            head, part, tail = SQL.partition("having")
            self._SQL = head + " limit {limit}"
            self.normal_data = False
        elif SQL.__contains__("{min}") and SQL.__contains__("{max}"):
            self._SQL = SQL + " limit {limit}"
            self.normal_data = True
        else:
            logger.error("The SQL Statement entered is invalid - it must contain a Having condition based"
                         "on expected normal minimums and maximums variables; {0} = min and {1} = max")
            sys.exit(-1)

    def _get_normal_request_data(self, conn, min, max):
        sql_var_dict = {"min": min, "max": max, "limit": self.max_pool_size}
        for value in self.required_fields.values():
            if isinstance(value, dict):
                for arg_name, arg_val in value.iteritems():
                    if isinstance(arg_name, str) and arg_name.startswith("arg"):
                        sql_var_dict.setdefault(arg_name, arg_val)

        querry = self._SQL.format(**sql_var_dict)
        try:
            with conn.cursor() as cur:
                cur.execute(querry)
                data = cur.fetchall()
                self.max_pool_size = len(data)

        except Exception as e:
            logger.exception(e)
            sys.exit(1)
        else:
            return data

    def _proccess_normal_request_data(self, normal_data, default_dict=None):
        if default_dict is None:
            default_dict = dict()
        json_data = []
        for key, value in self.required_fields.iteritems():
            if isinstance(value, list):
                default_dict.setdefault(key, value[0])
        for normal_row in normal_data:
            json = {}
            for key, value in self.required_fields.iteritems():
                if "pos" in value:
                    position = value["pos"]
                    json.setdefault(key, normal_row[position])
            json.update(**default_dict)
            json_data.append(json)

        return json_data

    def _is_optional_request_param(self, key, value):

        if key not in self.optional_fields:
            logger.error("{0} is not an accepted argument for this request; Accepted arguments {1}".format(key,
                                                                                                           self.optional_fields))
            return False
        key_values = self.optional_fields[key]
        if isinstance(key_values, list) and value not in key_values:
            logger.error(
                "{0} is not an acceted value for the key {1}. Accepted arguemnts for {1}: {2}".format(value, key,
                                                                                                      key_values))
            return False
        return True

    def _is_empty(self, attr):
        """
        A quick helper method to verify that inputs for the user recordings json are empty
        :param attr:
        :return:
        """
        if attr == "" or attr == None:
            return True
        else:
            return False

    def clean_optional_params(self):
        if self._is_succesful_init():
            remove = [x for x in self.normal_pool[0].keys() if x not in self.required_fields.keys()]
            for json in self.normal_pool:
                for to_be_removed in remove:
                    json.pop(to_be_removed)

    def _listify(self, json):
        if self.is_list:
            return [json]
        else:
            return json


class _TwoStateRequestPool(_ReadOnlyRequestPool):

    def __init__(self, sql, req_fields, opt_fields, min, max, start_state_params, end_state_params, is_list,
                 min_pool_size, max_pool_size):
        _ReadOnlyRequestPool.__init__(self, sql, req_fields, opt_fields, min, max, is_list, min_pool_size,
                                      max_pool_size)
        self.index = 0
        self.start_state_params = start_state_params
        self.end_state_params = end_state_params
        self.current_default_params = start_state_params

    def get_json(self, **kwargs):
        if not self._is_succesful_init():
            logger.error("JSON return is None because no data could be found")
            return
        try:
            json = self.normal_pool[self.index]
            self.index += 1
            return self._listify(json)
        except IndexError as e:
            self.flip_state()
            return self.get_json()

    def _proccess_normal_request_data(self, normal_data, default_dict=None):
        if default_dict is None:
            default_dict = dict()
        default_dict.update(**self.current_default_params)
        return super(_TwoStateRequestPool, self)._proccess_normal_request_data(normal_data, default_dict)

    def flip_state(self):
        self.index = 0
        self.clean_optional_params()
        if self.current_default_params is self.start_state_params:
            self.current_default_params = self.end_state_params
            self.add_optional_defualt_params(**self.current_default_params)
        else:
            self.current_default_params = self.start_state_params
            self.add_optional_defualt_params(**self.current_default_params)

    def close(self, url):
        self.clean_optional_params()
        self.current_default_params = self.end_state_params
        self.add_optional_defualt_params(**self.current_default_params)
        for json in self.normal_pool:
            to_send = self._listify(json)
            response = requests.post(url, json=to_send)
            assert response.status_code in [200, 404]


class _InverseStateRequestPool(_ReadOnlyRequestPool):
    pass
