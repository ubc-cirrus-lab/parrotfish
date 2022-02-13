import unittest
import boto3
import json
import spot

from unittest.mock import patch, call

from spot.logs.aws_log_retriever import AWSLogRetriever
from spot.db.db import DBClient


class TestLogRetrival(unittest.TestCase):
    def setUp(self) -> None:
        self.function = "AWSHelloWorld"
        self.logGroup = self.function
        self.timestamp = 0
        self.logRetriever = AWSLogRetriever(
            self.logGroup, "localhost", 27017, self.timestamp
        )
        self.allLogs = []

    def mock_get_log(self, logGroupName, logStreamName):
        print(f"trying to get {logGroupName} logs in {logStreamName}")
        log = {
            "events": [
                {
                    "timestamp": 100,
                    "message": f"REPORT RequestId: {logStreamName}	Duration: 1.50 ms	Billed Duration: 2 ms	Memory Size: 128 MB	Max Memory Used: 39 MB	Init Duration: 113.44 ms",
                    "ingestionTime": 123,
                },
            ]
        }
        self.allLogs.append(log)
        return log

    def mock_db_add(function_name, collection_name, document, criteria):
        print(f"Adding {criteria} to collection {collection_name}")

    @patch.object(
        spot.logs.aws_log_retriever.DBClient,
        "add_document_to_collection_if_not_exists",
        side_effect=mock_db_add,
    )
    @patch("spot.logs.aws_log_retriever.boto3")
    def test_get_logs(self, mockBoto3, mockDBAdd) -> None:
        # assert no logs for a certain timestamp in db
        stream = []
        with open("tests/sample_stream.json") as f:
            stream = json.load(f)
        mockBoto3.client("logs").describe_log_streams.return_value = stream
        mockBoto3.client("logs").get_log_events.new = self.mock_get_log
        mockBoto3.client("logs").get_log_events.side_effect = self.mock_get_log

        self.logRetriever.get_logs()

        logContent = {
            "timestamp": 100,
            "ingestionTime": 123,
            "Duration": "1.50",
            "Billed Duration": "2",
            "Memory Size": "128",
            "Max Memory Used": "39",
        }

        for s in stream["logStreams"]:
            logTemp = logContent
            name = s["logStreamName"]
            logTemp[
                "message"
            ] = f"REPORT RequestId: {name}\tDuration: 1.50 ms\tBilled Duration: 2 ms\tMemory Size: 128 MB\tMax Memory Used: 39 MB\tInit Duration: 113.44 ms"
            logTemp["RequestId"] = name
            callTemp = call(
                self.function,
                "logs",
                logTemp,
                {"RequestId": name},
            )
            mockDBAdd.assert_has_calls([callTemp])
