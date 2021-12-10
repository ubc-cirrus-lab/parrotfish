import os
import subprocess
import json 
from pymongo import MongoClient

class AWSLogRetriever:
    def __init__(self):
        super().__init__()
    def get_aws_logs(self, function_name = "AWSHelloWorld"):
        if not os.path.exists("logs/outputs"):
            os.makedirs("logs/outputs")
        #get groups => for now we only have 1 group and it is hard-coded below

        #get log streams
        streams = []
        response = subprocess.check_output(["aws", "logs", "describe-log-streams", "--log-group-name", function_name])
        response = json.loads(response)
        for stream in response["logStreams"]:
            streams.append((stream["logStreamName"]))

        #get log events and save it to json files
        for stream in streams:
            log = subprocess.check_output(["aws", "logs", "get-log-events", "--log-group-name", path, "--log-stream-name", stream])
            log = json.loads(log)
            log = json.dumps(log)
            stream = stream.replace('/', '.')
            with open("logs/outputs/" +stream + ".json", "w") as file:
                file.write(log)
    def save_to_db():
        client = MongoClient('localhost', 27017)

        db = client["mydb"]
        collection = db['aws_logs']

        outputs = os.listdir("logs/outputs")
        for output in outputs:
            with open("logs/outputs/"+output) as f:
                file_data = json.load(f)
                collection.insert_one(file_data)
        client.close()
