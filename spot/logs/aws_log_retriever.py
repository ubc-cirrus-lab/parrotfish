import os
import boto3
from spot.db.db import DBClient
from pymongo import MongoClient


class AWSLogRetriever:
    def __init__(self, function_name, url, port, last_log_timestamp):
        self.url = url
        self.port = port
        self.DBClient = DBClient(self.url, self.port)
        self.last_log_timestamp = last_log_timestamp
        self.function_name = function_name

    def get_logs(self):
        path = "/aws/lambda/" + self.function_name
        client = boto3.client('logs')
        return_value = self.last_log_timestamp

        # get log streams
        streams = []
        response = client.describe_log_streams(logGroupName=path)
        for stream in response["logStreams"]:
            if stream["lastEventTimestamp"] > self.last_log_timestamp:
                streams.append((stream["logStreamName"]))

        # get log events and save it to DB
        log_count = 0
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
                        log[field_name] = value
                    log["RequestId"] = requestId

                    # add log to db
                    return_value = max(log["timestamp"], return_value)
                    self.DBClient.add_document_to_collection_if_not_exists(
                        self.function_name, "logs", log, {"RequestId": requestId}
                    )
        return return_value

    def print_logs(self):
        iterator = self.DBClient.get_all_collection_documents(
            self.function_name, "logs"
        )
        for log in iterator:
            print(log)
