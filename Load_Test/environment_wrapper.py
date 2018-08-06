import json
import yaml
class EnvironmentWrapper:


    def __init__(self, env, **kwargs):
        self.__env = env
        info = self.__env.get("WRAP_INFO")
        self.info = {} if info is None else yaml.safe_load(info)
        for key, value in kwargs.iteritems():
            self.info[key] = value
        env["WRAP_INFO"] = json.dumps(self.info)




    def get(self, key):
        return self.info.get(key)



    def keys(self):
        return self.info.keys()



    def get_env(self):
        return self.__env




