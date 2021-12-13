import os
import subprocess
import json 
from pymongo import MongoClient

class DBClient:
    def __init__(self, url, port):
        self.url = url
        self.port = port
        
    # Creates database for the function name if the doesnt exist already
    def create_function_db(self, function_name):
        client = MongoClient(self.url, self.port)
        new_function_db = client[function_name]
        return


    def add_collection(self, function_name, collection_name):
        client = MongoClient(self.url, self.port)
        function_db = client[function_name]
        new_collection = function_db[collection_name]
        new_collection.insert_one({})
        return

    def add_document_to_collection(self, function_name, collection_name, document):
        client = MongoClient(self.url, self.port)
        function_db = client[function_name]
        collection = function_db[collection_name]
        collection.insert_one(document)
        return
    def add_document_to_collection_if_not_exists(self, function_name, collection_name, document, criteria, value):
        client = MongoClient(self.url, self.port)
        function_db = client[function_name]
        collection = function_db[collection_name]
        if not collection.find_one({criteria : value}):
            collection.insert_one(document)