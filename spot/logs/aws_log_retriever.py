import boto3
import pandas as pd
import re


class AWSLogRetriever:
    def __init__(self, function_name, max_log_count = None):
        self.function_name = function_name
        self.client = boto3.client("logs")
        self.max_log_count = max_log_count

    def get_logs(self, start_timestamp = None):
        path = f"/aws/lambda/{self.function_name}"
        next_token = None
        is_first = True

        response = []

        while next_token is not None or is_first:
            args = {
                "logGroupName": path,
                "orderBy": "LastEventTime",
                "descending": True,
            }
            if is_first:
                is_first = False
            else:
                args["nextToken"] = next_token

            stream_response = self.client.describe_log_streams(**args)

            next_token = stream_response.get("nextToken")

            is_newly_added = False
            for log_stream in stream_response["logStreams"]:
                args = {
                    "logGroupName": path,
                    "logStreamName": log_stream["logStreamName"],
                }
                if start_timestamp:
                    args["startTime"] = start_timestamp

                events = self.client.get_log_events(**args)["events"]
                for event in events:
                    if event["message"].startswith("REPORT"):
                        response.append(event)
                        is_newly_added = True

            if self.max_log_count and len(response) >= self.max_log_count:
                break

            if not is_newly_added:
                break

        return self._parse_logs(response)

    def _parse_logs(self, response):
        df = pd.DataFrame(response, columns=["timestamp", "message", "ingestionTime"])
        df["message"] = df["message"].str.replace("REPORT ", "")
        df["message"] = df["message"].str.replace(r"Init Duration:.*ms\t", "", regex=True)
        df["message"] = df["message"].str.replace(r"XRAY TraceId: [0-9a-f-]+\t", "", regex=True)
        df["message"] = df["message"].str.replace(r"SegmentId: [0-9a-f]+\t", "", regex=True)
        df["message"] = df["message"].str.replace(r"Sampled: (true|false)", "", regex=True)
        df["message"] = df["message"].str.replace(re.compile(r"(\n| |)"), "").str.rstrip("\t")

        df[["RequestId", "Duration", "Billed Duration", "Memory Size", "Max Memory Used"]] = df.message.str.split("\t", expand=True)
        df["RequestId"] = df["RequestId"].str.replace("RequestId:", "")

        df["Duration"] = df["Duration"].str.replace("Duration:", "")
        df["Duration"] = df["Duration"].str.replace("ms", "")
        df["Duration"] = df["Duration"].astype("float")

        df["Billed Duration"] = df["Billed Duration"].str.replace("BilledDuration:", "")
        df["Billed Duration"] = df["Billed Duration"].str.replace("ms", "")
        df["Billed Duration"] = df["Billed Duration"].astype("float")

        df["Memory Size"] = df["Memory Size"].str.replace("MemorySize:", "")
        df["Memory Size"] = df["Memory Size"].str.replace("MB", "")
        df["Memory Size"] = df["Memory Size"].astype("int")

        df["Max Memory Used"] = df["Max Memory Used"].str.replace("MaxMemoryUsed:", "")
        df["Max Memory Used"] = df["Max Memory Used"].str.replace("MB", "")
        df["Max Memory Used"] = df["Max Memory Used"].astype("int")

        df.drop(columns=["message"], inplace=True)
        return df

# if __name__ == "__main__":
#     pd.set_option('display.max_columns', 500)
#     pd.set_option('display.max_rows', 500)
#     pd.set_option('display.width', 1000)
#     pd.set_option('max_colwidth', -1)
#     r = AWSLogRetriever("VideoAnalyticsDecoder", 100)
#     df = r.get_logs()
#     print(df)
