import uuid
from uuid import uuid4
from API_Load_Test.Config.sql_route_statements import DATA_FACTORY_ROUTES
import requests
import json

class DataFactory:

    seinfield = {
        "guid": 'ea97e91c42104f958bab5c3691903a0c',
        "id": 919,
    }


    lsdvr = {

    }


    env_configuration = {
        "ribbons_user": {
            "total_users": 400,
            "rs": 200,
            "ls": 50,
            "franchise": 30, #have to wait for these to load
            "rules": 0
        },
        "update_settings_user": {
            "total_users": 400,
            "rs": 0,
            "ls": 0,
            "franchise": 0,
            "rules": 0
        },
        "protect_recordings_user": {
            "total_users": 1,
            "rs": 400,
            "ls": 0,
            "franchise": 0,
            "rules": 0
        },
        "update_rules_user": {
            "total_users": 400,
            "rs": 0,
            "ls": 0,
            "franchise": 0,
            "rules": 1
        },
        "list_rules_user": {
            "total_users": 400,
            "rs": 0,
            "ls": 0,
            "franchise": 0,
            "rules": 7
        },
        "recordings_user": {
            "total_users": 400,
            "rs": 0,
            "ls": 0,
            "franchise": 0,
            "rules": 0
        },
        "rules_user": {
            "total_users": 400,
            "rs": 400,
            "ls": 0,
            "franchise": 30,
            "rules": 0
        }

    }


    def __init__(self, config):

        self.config = config
        self.rs_recordings_table_name = "rsstuff_rsrecording"
        self.ls_recordings_table_name = "lsstuff_lsrecording"



    def configure_env(self, env, env_configuration = env_configuration):
        for desc in env_configuration.keys():
            conf = env_configuration[desc]



    def __execute_select_statement(self, query, env):
        conn = self.config.get_db_connection(env)
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                data = cur.fetchall()
                return data
        except Exception as e:
            raise e
        finally:
            conn.close()

    def __execute_commit_statement(self, query, env):
        conn = self.config.get_db_connection(env)
        try:
            with conn.cursor() as cur:
                count = cur.execute(query)
                conn.commit()
                return count
        except Exception as e:
            raise e
        finally:
            conn.close()

    def __pull_type_tables(self, ribbon_type, env, include_future = False, **kwargs):
        users_info = []
        if include_future:
            kwargs.setdefault("future", "")
        else:
            kwargs.setdefault("future", "r.rec_start < now() AND")
        if ribbon_type == "rs":
            kwargs.setdefault("table_name" , self.rs_recordings_table_name)
            querry = DATA_FACTORY_ROUTES["recs_exist"].format(**kwargs)
            users_info = self.__execute_select_statement(querry, env)
            users_info = [(user[0], int(user[1]), "rs") for user in users_info]
        elif ribbon_type == "ls":
            kwargs.setdefault("table_name", self.ls_recordings_table_name)
            querry = DATA_FACTORY_ROUTES["recs_exist"].format(**kwargs)
            users_info = self.__execute_select_statement(querry, env)
            users_info = [(user[0], int(user[1]), "rs") for user in users_info]
        elif ribbon_type == "both":
            kwargs.setdefault("table_name", self.rs_recordings_table_name)
            rs_querry = DATA_FACTORY_ROUTES["recs_exist"].format(**kwargs)
            kwargs.update(table_name=self.ls_recordings_table_name)
            ls_querry = DATA_FACTORY_ROUTES["recs_exist"].format(**kwargs)
            rs_user_info = self.__execute_select_statement(rs_querry, env)
            rs_user_info = [(user[0], int(user[1]), "rs") for user in rs_user_info]
            ls_user_info = self.__execute_select_statement(ls_querry, env)
            ls_user_info = [(user[0], int(user[1]), "ls") for user in ls_user_info]
            users_info = rs_user_info + ls_user_info
        return users_info


    def __get_bad_users(self, min_count, max_count, users_info):
        if len(users_info) == 0: #There were no users with the desc
            return []
        if max_count == None:
            bad_users = [user for user in users_info if min_count > user[1]]
        else:
            bad_users = [user for user in users_info if (min_count > user[1] or max_count < user[1])]
        if len(bad_users) == 0:
            return True
        else:
            return bad_users

    def __user_guid_taken(self, env, guid):
        querry = DATA_FACTORY_ROUTES["user_guid_taken"].format(guid=guid)
        user = self.__execute_select_statement(querry, env)
        return len(user) == 1

    def __get_user_guids_from_desc(self, env, desc):
        querry = DATA_FACTORY_ROUTES["user_guid_from_desc"].format(desc=desc)
        user_guids = self.__execute_select_statement(querry, env)
        return [user[0] for user in user_guids]


    def __get_franchise_ids(self, env, count):
        querry = DATA_FACTORY_ROUTES["get_franchise_ids"].format(count=count)
        franchises = self.__execute_select_statement(querry, env)
        return [franchise[0] for franchise in franchises]

    def __get_user_rule_info(self, env, user_guid):
        url = "{0}{1}".format(self.config.get_api_host(env, 1), self.config.get_api_route("List Rules", 4))
        to_post = {"user": user_guid}
        response = requests.post(url, json=to_post)
        assert response.status_code is 200
        rec_rules = json.loads(response.content)
        franchise_guids = []
        rule_guids = []
        for info in rec_rules["franchise_rules"]:
            franchise_guids.append(str(uuid.UUID(info["franchise"])))
            rule_guids.append(str(uuid.UUID(info["guid"])))
        return {"franchise": franchise_guids, "rule": rule_guids}

    def __get_rec_ids(self, env, count):
        querry = DATA_FACTORY_ROUTES["get_rec_ids"].format(count=count)
        rec_ids = self.__execute_select_statement(querry, env)
        return [(str(uuid.UUID(info[0])), str(uuid.UUID(info[1]))) for info in rec_ids]


    def __delete_users_guid(self, guids_list, env):
        query = DATA_FACTORY_ROUTES["delete_users"]
        for user_guid in guids_list:
            delete_query = query.format(guid=user_guid)
            self.__execute_commit_statement(delete_query, env)



    def users_count(self, env, desc = None):
        """
        See how many users with desc exist
        :param env: the environment you are checking for users
        :param desc: the description of specified users -- if None returns total number of users
        :return: True if min_count <= users in env where description = desc <= max_count, else False
        """
        querry = DATA_FACTORY_ROUTES["users_exist"]
        if desc == None:
            querry = querry.split("WHERE")[0]
        else:
            querry = querry.format(desc = desc)
        users = self.__execute_select_statement(querry, env)
        return len(users)

    def create_users(self, env, desc, count):
        url = "{0}{1}".format(self.config.get_api_host(env), self.config.get_api_route("Update User Settings", 1))
        json_to_post = {"user": "", "description": desc}
        for created_user_count in range(count):
            uuid = str(uuid4())
            while self.__user_guid_taken(env, uuid):
                uuid = str(uuid4())
            json_to_post["user"] = uuid
            response = requests.post(url, json=json_to_post)
            assert response.status_code is 200



    def delete_users(self, env, desc, remaining_count):
        user_guids = self.__get_user_guids_from_desc(env, desc)
        if len(user_guids) <= remaining_count:
            return
        else:
            user_guids = user_guids[remaining_count:]
            self.__delete_users_guid(user_guids, env)


    def recs_exist(self, min_count, max_count, env, desc, ribbon_type):
        """
        Check if user with description have enough show recordings -- find the ones that do not
        :param min_count: the minimum number of shows in the user recordings ribbon
        :param max_count: the maximum number of shows in the user recordings ribbon -- can be None
        :param env: the environment you are checking for users -> show recordings
        :param desc: the description of specified users
        :param ribbon_type: (VALUES: 'ls', 'rs', 'both') the location of recordings being pulled for recordings ribbon
        :return: True if all users (must > 0) w/ description = desc # of recordings in their ribbon is within bounds
                    else returns [(guid_that_failed_test_ex, show_rec_count), ...]
        """
        #standardize the user info
        users_info = self.__pull_type_tables(ribbon_type, env, desc=desc)
        return self.__get_bad_users(min_count, max_count, users_info)



    def create_recs(self, env, desc, count, ribbon_type):
        #THE ASSUMED USERS ARE THOUGHT TO HAVE TO PRIOR RECORDINGS
        #TODO: make lsdvr compatiable
        user_guids = self.__get_user_guids_from_desc(env, desc)
        rec_info = self.__get_rec_ids(env, count)
        url = "{host}{route}".format(host=self.config.get_api_host(env, 4), route=self.config.get_api_route("Create Recordings", 4))
        for user in user_guids:
            to_post = []
            for index in range(count):
                to_post.append({"user": user, "external_id": rec_info[index][0], "channel": rec_info[index][1]})
            response = requests.post(url, json=to_post)
            assert response.status_code is 200


    def franchise_recs_exist(self, min_count, max_count, env, desc, ribbon_type, franchise_guid):
        """
        Check if users with description have enough franchise recordings -- find the ones that do not
        :param min_count: the minimum number of shows in the specified franchise ribbon
        :param max_count: the maximum number of shows in the specified franchise ribbon -- can be None
        :param env: the environment you are checking for users -> franchise recordings
        :param desc: the description of the specified users
        :param ribbon_type: (VALUES: 'ls', 'rs', 'both') the location of recordings being pulled for franchise ribbon
        :param franchise_guid: the franchise_guid of the franchise you want to check
        :return: True if all users (must > 0) w/ description = desc # of recordings in the franchise is within bounds
                    else returns [(guid_that_failed_test_ex, franchise_rec_count), ...]
        """
        user_info = self.__pull_type_tables(ribbon_type, env, desc=desc, franchise_guid=franchise_guid)
        return self.__get_bad_users(min_count, max_count, user_info)
        pass #TODO: Finish when we can create recordings

    def create_franchise_recs(self, env, desc):
        pass





    def rules_exist(self, min_count, max_count, env, desc):
        """
        Check if users with description have enough rules -- find the ones that do not
        :param min_count: the minimum number of rules
        :param max_count: the maximum number of rules -- can be None
        :param env: the environment you are checking for users - > rules
        :param desc: the description of the specified users
        :return: True if all users (must > 0) w? description = desc # of rules is within bounds
                    else returns [(guid_that_failed_test_ex, num_rules_count), ...]

        """
        querry = DATA_FACTORY_ROUTES["rules_exist"].format(desc = desc)
        user_info = [(user[0], int(user[1])) for user in self.__execute_select_statement(querry, env)]
        return self.__get_bad_users(min_count, max_count, user_info)



    def create_rules(self, env, desc, count):
        #get user guids and find the max amount of rule guids we need
        user_guids = self.__get_user_guids_from_desc(env, desc)
        max_count = count
        url = "{host}{route}".format(host=self.config.get_api_host(env, 1), route=self.config.get_api_route("Create Rules",4))
        user_rules = {}
        #find out the max number of rules (assuming conflicts) so we only need to do one database interaction
        #store user guids and thier rule guids
        for user in user_guids:
            rule_franchise_guids = self.__get_user_rule_info(env, user)["franchise"]
            user_rule_count = count + len(rule_franchise_guids)
            if user_rule_count > max_count:
                max_count = user_rule_count
            user_rules.setdefault(user, rule_franchise_guids)
        querry = DATA_FACTORY_ROUTES["get_franchise_ids"].format(count=max_count)
        franchise_guids = [fran_guid[0] for fran_guid in self.__execute_select_statement(querry, env)]
        for user_id, existing_rules in user_rules.iteritems():
            set_rules = 0
            to_post = []
            for fran_guid in franchise_guids:
                if fran_guid in existing_rules:
                    continue
                else:
                    to_post.append({"user": user_id, "type": "franchise", "franchise": fran_guid, "mode": "new"})
                    set_rules = set_rules + 1
                if set_rules == count:
                    break
            assert len(to_post) is count
            response = requests.post(url, json=to_post)
            assert response.status_code is 200


    def delete_rules(self, env, desc, remaining_count):
        url = "{host}{route}".format(host=self.config.get_api_host(env, 0), route=self.config.get_api_route("Delete Rules", 1))
        user_guids = self.__get_user_guids_from_desc(env, desc)
        for user in user_guids:
            rule_guids = self.__get_user_rule_info(env, user)["rule"]
            if len(rule_guids) <= remaining_count:
                continue
            else:
                rule_guids = rule_guids[remaining_count:]
                to_post = [{"type": "franchise", "guid": rule_guid} for rule_guid in rule_guids]
                response = requests.post(url, json=to_post)
                assert response.status_code is 200
























