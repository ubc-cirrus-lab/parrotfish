import os
import subprocess
import json 
import time as time
from spot.db.db import DBClient
from pymongo import MongoClient
import datetime

class AWSConfigRetriever:
    def __init__(self, function_name, url, port):
        self.url = url
        self.port = port
        self.DBClient = DBClient(self.url, self.port) 
        self.function_name = function_name
        
    def get_latest_config(self):
        config = subprocess.check_output(["aws", "lambda", "get-function-configuration", "--function-name", self.function_name])
        config = json.loads(config)
        date = datetime.datetime.strptime(config["LastModified"], '%Y-%m-%dT%H:%M:%S.%f+0000')
        timestamp = str((date - datetime.datetime(1970, 1, 1)).total_seconds()*1000)
        config["LastModifiedInMs"] = int(timestamp[:-2])
        config["Architectures"] = config["Architectures"][0]
        self.DBClient.add_new_config_if_changed(self.function_name, "config", config)
        
        #client.disconnect()
    def print_configs(self):
        iterator = self.DBClient.get_all_collection_documents(self.function_name, "config")
        for config in iterator:
            print(config)

'''
a = AWSConfigRetriever("AWSHelloWorld", "localhost", 27017 )
a.get_latest_config()
'''