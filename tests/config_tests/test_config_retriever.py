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
        self.db = DBClient()
        self.configRetriever = AWSConfigRetriever(self.function, self.db)

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
            last_modified = datetime.datetime.strptime(
                sample_config["LastModified"], "%Y-%m-%dT%H:%M:%S.%f%z"
            )
            last_modified_ms = int(last_modified.timestamp() * 1000)
            sample_config["LastModifiedInMs"] = str(last_modified_ms)

            sample_config["Architectures"] = sample_config["Architectures"][0]
            callTemp = call(self.function, "config", sample_config)
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

            # assert a database call to get_all_collection_documents has been made with proper variables
            callTemp = call(self.function, "config")
            mockDBClient.assert_has_calls([callTemp])


if __name__ == "__main__":
    unittest.main()
