import boto3
import time
from botocore.exceptions import WaiterError
from moto import mock_logs
from botocore.stub import Stubber
from unittest import TestCase
from unittest.mock import MagicMock, patch
from datetime import datetime


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
        self.client = logs
        self.queryWaiter = LogQueryWaiter(logs)

    def test_wait_success(self):
        query = f'fields @timestamp, @memorySize, @billedDuration, @requestId \
                | filter (@timestamp>0) \
                | filter @type="REPORT" | limit 1'
        query_id = self.client.start_query(
            logGroupName=self.log_group_name,
            startTime=0,
            endTime=int(datetime.now().timestamp()),
            queryString=query,
        )["queryId"]
        with patch("spot.logs.custom_waiter.botocore.waiter.Waiter.wait", new=self._mock_wait):
            self.queryWaiter.wait(query_id=query_id)

    def _mock_wait(self, *args, **kwargs):
        time.sleep(3)
