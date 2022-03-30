import boto3

from unittest import TestCase
from unittest.mock import MagicMock, patch
from moto import mock_logs
from botocore.exceptions import WaiterError
from datetime import datetime

from spot.logs.log_propagation_waiter import LogPropagationWaiter, LOG_TIMEOUT, LOG_WAIT_SLEEP_TIME


@mock_logs
class LogPropagationWaiterTest(TestCase):
    def setUp(self) -> None:
        logs = boto3.client("logs")
        func = "test_function"
        group = "/aws/lambda/" + func
        stream = "test_stream"
        logs.create_log_group(logGroupName=group)
        logs.create_log_stream(logGroupName=group, logStreamName=stream)
        logs.get_query_results = MagicMock(
            return_value={
                "results": [
                    [{"field": "@timestamp", "value": "2000-03-30 0:0:0.0"}],
                ],
                "status": "Complete",
            }
        )
        # self.client = logs
        self.log_prop_waiter = LogPropagationWaiter(func)
        self.log_prop_waiter.client = logs

    @patch("time.sleep", return_value=True)
    def test_wait_timeout(self, mock_sleep):
        self.log_prop_waiter.wait(start=datetime.now().timestamp())
        self.assertEqual(mock_sleep.call_count, LOG_TIMEOUT/LOG_WAIT_SLEEP_TIME)
