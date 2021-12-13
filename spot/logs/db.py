import os
import json
from pymongo import MongoClient

client = MongoClient('localhost', 27017)

db = client["mydb"]
collection = db['aws_logs']

outputs = os.listdir("outputs")
for output in outputs:
    with open("outputs/"+output) as f:
        file_data = json.load(f)
        collection.insert_one(file_data)
client.close()
