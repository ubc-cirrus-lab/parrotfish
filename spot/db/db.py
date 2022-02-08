import os
import subprocess
import json
from pymongo import MongoClient
import pymongo


class DBClient:
    # TODO: Can change creating mongoclient on constructor instead of in every function
    def __init__(self, url, port):
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

    def add_new_config_if_changed(self, function_name, collection_name, document):
        function_db = self.client[function_name]
        collection = function_db[collection_name]

        latest_config = collection.find_one(sort=[("_id", pymongo.DESCENDING)])
        if latest_config:
            del latest_config["_id"]
            del latest_config["LastModified"]
            del latest_config["RevisionId"]
            del latest_config["LastModifiedInMs"]

        test = document.copy()
        del test["LastModified"]
        del test["RevisionId"]

        if not latest_config == test:
            collection.insert_one(document)

    def execute_query(
        self, function_name, collection_name, select_fields, display_fields
    ):
        function_db = self.client[function_name]
        collection = function_db[collection_name]
        return collection.find(select_fields, display_fields)
