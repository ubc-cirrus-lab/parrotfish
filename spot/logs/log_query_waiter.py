from enum import Enum
import time
from datetime import datetime

import boto3
import botocore
from botocore.waiter import WaiterModel
from botocore.waiter import create_waiter_with_client

from spot.logs.custom_waiter import CustomWaiter, WaitState

LOG_TIMEOUT = 60
LOG_WAIT_SLEEP_TIME = 15


class LogQueryWaiter(CustomWaiter):
    """Wait for a log query to finish"""

    def __init__(self, client, delay=10, max_tries=60, matcher="path"):
        acceptors = {"Complete": WaitState.SUCCESS, "Failed": WaitState.FAILURE}
        super().__init__(
            "LogQueryComplete",
            "GetQueryResults",
            "status",
            acceptors,
            client,
            delay,
            max_tries,
            matcher,
        )

    def wait(self, query_id: str) -> None:
        self._wait(queryId=query_id)