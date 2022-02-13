import unittest
import json
from unittest.mock import patch, call
import datetime

import spot
from spot.configs.aws_config_retriever import AWSConfigRetriever
from spot.db.db import DBClient


class TestConfigRetrieval(unittest.TestCase):
    def setUp(self) -> None:
        self.function = "AWSHelloWorld"
        self.timestamp = 0
        self.configRetriever = AWSConfigRetriever(self.function, "localhost", 27017)

    @patch.object(
        spot.configs.aws_config_retriever.DBClient, "add_new_config_if_changed"
    )
    @patch("spot.configs.aws_config_retriever.boto3")
    def test_get_latest_config(self, mockBoto3, mockDBClient):
        sample_config = []
        with open("tests/config_tests/sample_function_configuration.json") as f:
            sample_config = json.load(f)
            mockBoto3.client(
                "lambda"
            ).get_function_configuration.return_value = sample_config
            self.configRetriever.get_latest_config()

            # assert a database call has been made with function add_new_config_if_changed with appropriate variables
            configTemp = sample_config
            date = datetime.datetime.strptime(
                configTemp["LastModified"], "%Y-%m-%dT%H:%M:%S.%f+0000"
            )
            timestamp = str(
                (date - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
            )
            configTemp["LastModifiedInMs"] = int(timestamp[:-2])
            configTemp["Architectures"] = configTemp["Architectures"][0]
            callTemp = call(self.function, "config", configTemp)
            mockDBClient.assert_has_calls([callTemp])

    @patch.object(
        spot.configs.aws_config_retriever.DBClient, "get_all_collection_documents"
    )
    def test_print_configs(self, mockDBClient):
        sample_config = []
        with open("tests/config_tests/sample_function_configuration.json") as f:
            sample_config = json.load(f)
            mockDBClient.get_all_collection_documents.return_value = [sample_config]
            self.configRetriever.print_configs()


if __name__ == "__main__":
    unittest.main()
