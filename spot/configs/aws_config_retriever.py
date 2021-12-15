import os
import subprocess
import json 
import time as time
from spot.db.db import DBClient
from pymongo import MongoClient

class AWSConfigRetriever:
    def __init__(self):
        super().__init__()

    def get_previous_config(self, app_name, time):
        pass
        
    def get_latest_config(self, function_name = "AWSHelloWorld"):
        client = DBClient("localhost", 27017) 

        config = subprocess.check_output(["aws", "lambda", "get-function-configuration", "--function-name", function_name])
        config = json.loads(config)
        #Fix this
        client.add_new_config_if_changed(function_name, "config", config)
        
        #client.disconnect()
    def print_configs(self, function_name = "AWSHelloWorld"):
        client = DBClient("localhost", 27017) 
        iterator = client.get_all_collection_documents(function_name, "config")
        for config in iterator:
            print(config)