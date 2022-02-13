import boto3
import time as time
import datetime

from spot.logs.aws_log_retriever import AWSLogRetriever
from spot.db.db import DBClient
from unittest.mock import patch, call


class AWSConfigRetriever:
    def __init__(self, function_name, url, port):
        self.url = url
        self.port = port
        self.DBClient = DBClient(self.url, self.port)
        self.function_name = function_name

    def get_latest_config(self):
        client = boto3.client("lambda")
        config = client.get_function_configuration(FunctionName=self.function_name)
        date = datetime.datetime.strptime(
            config["LastModified"], "%Y-%m-%dT%H:%M:%S.%f+0000"
        )
        timestamp = str((date - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)
        config["LastModifiedInMs"] = int(timestamp[:-2])
        config["Architectures"] = config["Architectures"][0]
        self.DBClient.add_new_config_if_changed(self.function_name, "config", config)

    def print_configs(self):
        iterator = self.DBClient.get_all_collection_documents(
            self.function_name, "config"
        )
        for config in iterator:
            print(config)
