import time
import boto3
from datetime import datetime

from spot.logs.log_query_waiter import LogQueryWaiter


class LogPropWaiterTimeoutError(Exception):
    pass


class LogPropagationWaiter:
    """Waits for CloudWatch log to propagate after invocation

    Args:
        function_name: the name of the function to wait on
    Raises:
        LogPropWaiterTimeoutError: if fails to read the target number of logs after retrying
    """

    def __init__(self, function_name: str) -> None:
        self._client = boto3.client("logs")
        self._function_name = function_name

    def wait(
        self,
        start: float,
        prev_timestamp: float = 0,
        retry: int = 10,
        wait_interval: int = 15,
    ):
        """Wait by checking the timestamp of the most recent log"""
        last_log_time = self._most_recent_log_time(start)

        while last_log_time != prev_timestamp:
            if not retry:
                print(
                    f"Log propagation waiter timed out after retrying for {retry} times"
                )
                return
            if last_log_time > start:
                prev_timestamp = last_log_time
            else:
                retry -= 1
            time.sleep(wait_interval)
            last_log_time = self._most_recent_log_time(start)

        print(f"log propagated, {last_log_time = }")

    def wait_by_count(
        self,
        start: float,
        log_cnt: int,
        retry: int = 10,
        wait_interval: int = 15,
    ) -> None:
        """Wait by checking the number of new logs"""
        new_log_cnt = 0
        while new_log_cnt < log_cnt:
            time.sleep(wait_interval)
            temp = self._get_new_logs_cnt(start)
            while new_log_cnt == temp and retry:
                time.sleep(wait_interval)
                temp = self._get_new_logs_cnt(start)
                retry -= 1
            new_log_cnt = temp
            if not retry:
                print(f"max retry reached, got {new_log_cnt}/{log_cnt} logs")
                raise (LogPropWaiterTimeoutError)

        last_log_time = self._most_recent_log_time(start)
        print(f"log propagated, {last_log_time = }")

    def _get_new_logs_cnt(self, start: float) -> int:
        log_group = "/aws/lambda/" + self._function_name
        query_id = self._client.start_query(
            logGroupName=log_group,
            startTime=int(start),
            endTime=int(datetime.now().timestamp()),
            queryString='filter @type = "REPORT"',
        )["queryId"]
        LogQueryWaiter(self._client).wait(query_id=query_id)
        res = self._client.get_query_results(queryId=query_id)["results"]
        return len(res)

    def _most_recent_log_time(self, start: float) -> float:
        log_group = "/aws/lambda/" + self._function_name
        get_log_query = "fields @timestamp | sort @timestamp desc | limit 1"
        query_id = self._client.start_query(
            logGroupName=log_group,
            startTime=int(start),
            endTime=int(datetime.now().timestamp()),
            queryString=get_log_query,
            limit=1,
        )["queryId"]
        LogQueryWaiter(self._client).wait(query_id=query_id)

        res = self._client.get_query_results(queryId=query_id)["results"][0]
        log_time = self._get_query_value(res, "@timestamp")
        log_datetime = datetime.strptime(log_time, "%Y-%m-%d %H:%M:%S.%f")
        log_timestamp = log_datetime.timestamp()
        return log_timestamp

    def _get_query_value(self, query_res: list, field: str) -> str:
        for fv in query_res:
            f = fv["field"]
            v = fv["value"]
            if f == field:
                return v
        return None
