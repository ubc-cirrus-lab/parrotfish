import boto3
import time
from botocore.exceptions import WaiterError
from moto import mock_logs
from botocore.stub import Stubber
from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import datetime

# from botocore.client import CloudWatchLogs

from spot.logs.log_query_waiter import LogQueryWaiter


@mock_logs
class QueryWaiterTest(TestCase):
    def setUp(self) -> None:
        self.log_group_name = "test-group"
        log_stream_name = "test-stream"
        logs = boto3.client("logs")
        logs.create_log_group(logGroupName=self.log_group_name)
        logs.create_log_stream(
            logGroupName=self.log_group_name,
            logStreamName=log_stream_name,
        )
        logs.get_query_results = MagicMock(return_value={"status": "Complete"})
        # logs.start_query = MagicMock(return_value={"queryId": "testId"})
        self.client = logs
        self.queryWaiter = LogQueryWaiter(self.client)
        self.queryWaiter.client.get_query_results = MagicMock(
            return_value={"status": "Complete"}
        )

    # @patch("spot.logs.logs_waiter.boto3")
    def test_query_wait_invalid_id(self):
        # mock_boto3.client = self.mock_boto3_client
        with self.assertRaises(WaiterError):
            self.queryWaiter.wait("")

    @patch("spot.logs.logs_waiter.boto3")
    def test_new(self, mock_boto3):
        mock_boto3.client = self.mock_boto3_client
        query = f'fields @timestamp, @memorySize, @billedDuration, @requestId \
                | filter (@timestamp>0) \
                | filter @type="REPORT" | limit 1'
        query_id = self.client.start_query(
            logGroupName=self.log_group_name,
            startTime=0,
            endTime=int(datetime.now().timestamp()),
            queryString=query,
        )["queryId"]
        # self.queryWaiter.get_query_results = MagicMock(return_value={"status": "Complete"})
        with patch("spot.logs.custom_waiter.botocore.waiter.Waiter") as mock_waiter:
            mock_waiter.wait = self._mock_func
            self.queryWaiter.wait(query_id=query_id)

    def _mock_func(self, *args, **kwargs):
        time.sleep(3)
        print(kwargs)
        return {"status": "Complete"}

    def mock_boto3_client(*args, **kwargs):
        mock_client = boto3.client(*args, **kwargs)
        if args[0] == "logs":
            # Use MagicMock.
            mock_client.get_query_results = MagicMock(
                return_value={"status": "Complete"}
            )
        return mock_client
