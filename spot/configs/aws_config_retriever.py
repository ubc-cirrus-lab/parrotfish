import os
import subprocess
import json 
import time as time
from pymongo import MongoClient

class AWSConfigRetriever:
    def __init__(self):
        super().__init__()
    
    def get_latest_config(self, app_name):
        #print("This function gets latest configs for the app: ", app_name)
        pass

    def get_previous_config(self, app_name, time):
        pass
        
    def get_aws_configs(self, function_name = "AWSHelloWorld"):
        if not os.path.exists("configs/outputs"):
            os.makedirs("configs/outputs")

        #get config and save it to json
        config = subprocess.check_output(["aws", "lambda", "get-function-configuration", "--function-name", function_name])
        config = json.loads(config)
        config = json.dumps(config)
        with open("configs/outputs/" +str(int(time.time())) + ".json", "w") as file:
            file.write(config)

    def save_to_db(data):
        client = MongoClient('localhost', 27017)

        db = client["mydb"]
        collection = db['aws_configs']

        outputs = os.listdir("configs/outputs")
        for output in outputs:
            with open("configs/outputs/"+output) as f:
                file_data = json.load(f)
                collection.insert_one(file_data)
        client.close()