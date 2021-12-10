import os
import subprocess
import json 

def get_aws_logs(function_name = "AWSHelloWorld"):
    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    #get groups => for now we only have 1 group and it is hard-coded below

    #get log streams
    streams = []
    response = subprocess.check_output(["aws", "logs", "describe-log-streams", "--log-group-name", "/aws/lambda/"+function_name])
    response = json.loads(response)
    for stream in response["logStreams"]:
        streams.append((stream["logStreamName"]))

    #get log events and save it to json files
    for stream in streams:
        log = subprocess.check_output(["aws", "logs", "get-log-events", "--log-group-name", "/aws/lambda/"+function_name, "--log-stream-name", stream])
        log = json.loads(log)
        log = json.dumps(log)
        stream = stream.replace('/', '.')
        with open("outputs/" +stream + ".json", "w") as file:
            file.write(log)

get_aws_logs()