import time
import boto3
from datetime import datetime

from spot.logs.log_query_waiter import LogQueryWaiter


LOG_TIMEOUT = 60
LOG_WAIT_SLEEP_TIME = 15


class LogPropagationWaiter:
    """Waits for CloudWatch log to propagate after invocation"""

    def __init__(self, function_name):
        self.client = boto3.client("logs")
        self.function_name = function_name

    def wait(self, start, prev_timestamp=0):
        recent_log_time = self.most_recent_log_time()
        retry = LOG_TIMEOUT

        while recent_log_time != prev_timestamp:  # new log fetched
            if not retry:
                print(
                    f"waited for log timed out after {LOG_TIMEOUT}s, no new log available"
                )
                return
            if recent_log_time > start:
                prev_timestamp = recent_log_time
            else:
                retry -= LOG_WAIT_SLEEP_TIME
            time.sleep(LOG_WAIT_SLEEP_TIME)
            recent_log_time = self.most_recent_log_time()

        # print("log propagated, now continue to fetch logs from cloud")

    def most_recent_log_time(self) -> float:
        log_group = "/aws/lambda/" + self.function_name
        get_log_query = "fields @timestamp | sort @timestamp desc | limit 1"
        query_id = self.client.start_query(
            logGroupName=log_group,
            startTime=0,  # TODO: bug? if set to self.last_log_timestamp then has error of start tiem is after end time
            endTime=int(datetime.now().timestamp()),
            queryString=get_log_query,
            limit=1,
        )["queryId"]
        LogQueryWaiter(self.client).wait(query_id=query_id)

        res = self.client.get_query_results(queryId=query_id)["results"][0]
        log_time = self.get_query_value(res, "@timestamp")
        log_datetime = datetime.strptime(log_time, "%Y-%m-%d %H:%M:%S.%f")
        log_timestamp = log_datetime.timestamp()
        return log_timestamp

    def get_query_value(self, query_res: list, field: str) -> str:
        for fv in query_res:
            f = fv["field"]
            v = fv["value"]
            if f == field:
                return v
        return None
