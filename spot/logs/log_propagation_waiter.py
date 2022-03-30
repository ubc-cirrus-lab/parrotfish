from os import waitid_result
import time
import boto3
from datetime import datetime

from spot.logs.log_query_waiter import LogQueryWaiter


class LogPropagationWaiter:
    """Waits for CloudWatch log to propagate after invocation"""

    def __init__(self, function_name):
        self.client = boto3.client("logs")
        self.function_name = function_name

    def wait(self, start, prev_timestamp=0, retry=10, wait_interval=15):
        last_log_time = self.most_recent_log_time(start)

        while last_log_time != prev_timestamp:
            if not retry:
                print(f"Log propagation waiter timed out after retrying for {retry} times")
                return
            if last_log_time > start:
                prev_timestamp = last_log_time
            else:
                retry -= 1
            time.sleep(wait_interval)
            last_log_time = self.most_recent_log_time(start)

        print(f"log propagated, {last_log_time = }")

    def wait_by_count(self, start, log_cnt, retry=10, wait_interval=15):
        new_log_cnt = 0
        while new_log_cnt != log_cnt:
            time.sleep(wait_interval)
            temp = self.get_new_logs_cnt(start)
            while new_log_cnt == temp and retry:
                time.sleep(wait_interval)
                temp = self.get_new_logs_cnt(start)
                retry -= 1
            new_log_cnt = temp
            if not retry:
                print(f"max {retry=} reached, got {new_log_cnt}/{log_cnt} logs")
                return

        last_log_time = self.most_recent_log_time(start)
        print(f"log propagated, {last_log_time = }")
        

    def get_new_logs_cnt(self, start):
        log_group = "/aws/lambda/" + self.function_name
        # get_log_query = "fields @timestamp | sort @timestamp desc | limit 1"
        query_id = self.client.start_query(
            logGroupName=log_group,
            # startTime=int(start),
            startTime=int(start),
            endTime=int(datetime.now().timestamp()),
            queryString='filter @type = "REPORT"',
        )["queryId"]
        LogQueryWaiter(self.client).wait(query_id=query_id)
        res = self.client.get_query_results(queryId=query_id)["results"]
        return len(res)


    def most_recent_log_time(self, start) -> float:
        log_group = "/aws/lambda/" + self.function_name
        get_log_query = "fields @timestamp | sort @timestamp desc | limit 1"
        query_id = self.client.start_query(
            logGroupName=log_group,
            # startTime=int(start),
            startTime=0,
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
