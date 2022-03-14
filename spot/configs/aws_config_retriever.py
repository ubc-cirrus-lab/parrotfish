import os
import boto3
import time as time
from spot.db.db import DBClient
import datetime


class AWSConfigRetriever:
    def __init__(self, function_name, db: DBClient):
        self.DBClient = db
        self.function_name = function_name

    def get_latest_config(self):
        client = boto3.client("lambda")
        config = client.get_function_configuration(FunctionName=self.function_name)

        last_modified = datetime.datetime.strptime(
            config["LastModified"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        last_modified_ms = int(last_modified.timestamp() * 1000)
        config["LastModifiedInMs"] = str(last_modified_ms)

        config["Architectures"] = config["Architectures"][0]
        self.DBClient.add_new_config_if_changed(self.function_name, "config", config)

    def print_configs(self):
        iterator = self.DBClient.get_all_collection_documents(
            self.function_name, "config"
        )
        for config in iterator:
            print(config)
