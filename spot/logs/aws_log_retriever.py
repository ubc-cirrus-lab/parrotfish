import boto3
from spot.db.db import DBClient
from spot.constants import *
import re


class AWSLogRetriever:
    def __init__(self, function_name, db: DBClient, last_log_timestamp):
        self.DBClient = db
        self.last_log_timestamp = last_log_timestamp
        self.function_name = function_name

    def get_logs(self):
        path = "/aws/lambda/" + self.function_name
        client = boto3.client("logs")
        new_timestamp = self.last_log_timestamp

        # get log streams
        streams = []
        next_token = ""
        new_logs = True
        while new_logs:
            response = client.describe_log_streams(logGroupName=path, orderBy="LastEventTime", descending=True, nextToken=next_token) if next_token != "" else client.describe_log_streams(logGroupName=path, orderBy="LastEventTime", descending=True)

            for stream in response["logStreams"]:
                if stream["lastEventTimestamp"] > self.last_log_timestamp:
                    streams.append((stream["logStreamName"]))
                else:
                    new_logs = False
                    break
            if next_token == response["nextToken"] or response["nextToken"] == "":
                break
            next_token = response["nextToken"]

        # get log events and save it to DB
        for stream in streams:
            logs = client.get_log_events(logGroupName=path, logStreamName=stream)

            # parse and reformat log
            for log in logs["events"]:
                if log["message"].startswith("REPORT"):
                    request_id_start_pos = log["message"].find(":") + 2
                    request_id_end_pos = log["message"].find("\t")
                    requestId = log["message"][request_id_start_pos:request_id_end_pos]
                    message_sections = log["message"].split("\t")
                    for message_section in message_sections[1:-1]:
                        field_name = message_section.split(":")[0]
                        value = message_section.split(":")[1][1:].split(" ")[0]
                        if re.match(r"^[0-9]+\.[0-9]+$", value):
                            log[field_name] = float(value)
                        elif re.match(r"^[0-9]+$", value):
                            log[field_name] = int(value)
                        else:
                            log[field_name] = value
                    log[REQUEST_ID] = requestId

                    # add log to db
                    new_timestamp = max(log[TIMESTAMP], new_timestamp)
                    self.DBClient.add_document_to_collection_if_not_exists(
                        self.function_name, DB_NAME_LOGS, log, {REQUEST_ID: requestId}
                    )

        return new_timestamp

    def print_logs(self):
        iterator = self.DBClient.get_all_collection_documents(
            self.function_name, DB_NAME_LOGS
        )
        for log in iterator:
            print(log)
