import os
import subprocess
import json 
from spot.db.db import DBClient
from pymongo import MongoClient

class AWSLogRetriever:
    def __init__(self, function_name, url, port):
        self.url = url
        self.port = port
        self.DBClient = DBClient(self.url, self.port) 
        
        self.function_name = function_name
   
    def get_logs(self):
        path = "/aws/lambda/" + self.function_name

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

            #parse and reformat log
            log = log["events"][2]
            request_id_start_pos = log["message"].find(":")+2
            request_id_end_pos = log["message"].find("\t")
            requestId = log["message"][request_id_start_pos:request_id_end_pos]
            message_sections = log["message"].split("\t")
            for message_section in message_sections[1:-1]:
                field_name = message_section.split(":")[0]
                value = message_section.split(":")[1][1:].split(" ")[0]
                log[field_name] = value
            log["RequestId"] = requestId

            #add log to db
            self.DBClient.add_document_to_collection_if_not_exists(self.function_name, "logs", log, {"RequestId" : requestId})

        #client.close()
    def print_logs(self):
        iterator = self.DBClient.get_all_collection_documents(self.function_name, "logs")
        for log in iterator:
            print(log)
