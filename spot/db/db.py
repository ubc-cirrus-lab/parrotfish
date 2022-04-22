import os
import subprocess
import json
from pymongo import MongoClient
import pymongo


class DBClient:
    def __init__(self, url="localhost", port=27017):
        self.url = url
        self.port = port
        self.client = MongoClient(self.url, self.port)

    # Creates database for the function name if the doesnt exist already
    def create_function_db(self, function_name):
        new_function_db = self.client[function_name]
        return

    def add_collection(self, function_name, collection_name):
        function_db = self.client[function_name]
        new_collection = function_db[collection_name]
        new_collection.insert_one({})
        return

    def get_all_collection_documents(self, function_name, collection_name):
        function_db = self.client[function_name]
        collection = function_db[collection_name]
        return collection.find()

    def add_document_to_collection(self, function_name, collection_name, document):
        function_db = self.client[function_name]
        collection = function_db[collection_name]
        collection.insert_one(document)
        return

    def add_document_to_collection_if_not_exists(
        self, function_name, collection_name, document, criteria
    ):
        function_db = self.client[function_name]
        collection = function_db[collection_name]
        if not collection.find_one(criteria):
            collection.insert_one(document)

    def remove_document_from_collection(self, function_name, collection_name, query):
        function_db = self.client[function_name]
        collection = function_db[collection_name]
        collection.delete_one(query)

    def add_new_config_if_changed(self, function_name, collection_name, document):
        function_db = self.client[function_name]
        collection = function_db[collection_name]

        latest_saved_config = collection.find_one(sort=[("_id", pymongo.DESCENDING)])

        # Delete unique identifier fields to be able to configure current and most recent config
        if latest_saved_config:
            del latest_saved_config["_id"]
            del latest_saved_config["LastModified"]
            del latest_saved_config["RevisionId"]
            del latest_saved_config["LastModifiedInMs"]
            del latest_saved_config["ResponseMetadata"]

        current_config = document.copy()
        del current_config["LastModified"]
        del current_config["LastModifiedInMs"]
        del current_config["RevisionId"]
        del current_config["ResponseMetadata"]

        if not latest_saved_config == current_config:
            collection.insert_one(document)
        elif not current_config.keys() == latest_saved_config.keys():
            print("Warning: AWS might have changed configuration parameters")

    def execute_query(
        self, function_name, collection_name, select_fields, display_fields
    ):
        function_db = self.client[function_name]
        collection = function_db[collection_name]
        return collection.find(select_fields, display_fields)

    def execute_max_value(self, function_name: str, collection_name: str, field: str):
        function_db = self.client[function_name]
        collection = function_db[collection_name]
        return collection.find().sort(f"{field}", -1).limit(1)[0][field]

    def get_top_docs(self, function_name: str, collection_name: str, doc_cont: int):
        function_db = self.client[function_name]
        collection = function_db[collection_name]
        return collection.find(sort=[("_id", pymongo.DESCENDING)]).limit(doc_cont)
