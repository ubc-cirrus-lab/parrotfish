import os
import subprocess
import json 
from spot.db.db import DBClient
from pymongo import MongoClient

class AWSLogRetriever:
    def __init__(self):
        super().__init__()
    def get_aws_logs(self, function_name = "AWSHelloWorld"):
        client = DBClient("localhost", 27017) 
        path = "/aws/lambda/" + function_name

        #get log streams
        streams = []
        response = subprocess.check_output(["aws", "logs", "describe-log-streams", "--log-group-name", path])
        response = json.loads(response)
        for stream in response["logStreams"]:
            streams.append((stream["logStreamName"]))

        #get log events and save it to DB
        for stream in streams:
            log = subprocess.check_output(["aws", "logs", "get-log-events", "--log-group-name", path, "--log-stream-name", stream])
            log = json.loads(log)
            log = log["events"][2]
            request_id_start_pos = log["message"].find(":")+2
            request_id_end_pos = log["message"].find("\t")
            requestId = log["message"][request_id_start_pos:request_id_end_pos]
            log["RequestId"] = requestId
            client.add_document_to_collection_if_not_exists(function_name, "logs", log, "RequestId",requestId)
