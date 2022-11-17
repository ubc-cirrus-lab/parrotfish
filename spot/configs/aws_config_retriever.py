import boto3
import datetime


class AWSConfigRetriever:
    def __init__(self, function_name):
        self.function_name = function_name

    def get_latest_config(self):
        client = boto3.client("lambda")
        config = client.get_function_configuration(FunctionName=self.function_name)

        last_modified = datetime.datetime.strptime(
            config["LastModified"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        last_modified_ms = int(last_modified.timestamp() * 1000)
        config["LastModifiedInMs"] = int(last_modified_ms)
        config["Architectures"] = config["Architectures"][0]
