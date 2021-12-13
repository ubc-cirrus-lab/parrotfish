from spot.prices.price_retriever import PriceRetriever
import os
import json
from pymongo import MongoClient
import time as time

class AWSPriceRetriever(PriceRetriever):
    def __init__(self):
        super().__init__()

    def get_current_prices(self, region="us-east-1") -> dict:
        """
        Returns the price per request and price per second as a dictionary

        Keyword arguments:
        Region -- the AWS region for pricing information (default "us-east-1")
        """
        parameters = {"vendor": "aws", "service": "AWSLambda", "family": "Serverless", "region": region, "type": "AWS-Lambda-Requests", "purchaseOption": "on_demand"}
        request_price = self._current_price(parameters)
        parameters["type"] = "AWS-Lambda-Duration"
        duration_price = self._current_price(parameters)
        return {"timestamp":int(time.time()),"per_request": request_price, "per_gb_second": duration_price}

    def save_to_db(data):
        client = MongoClient('localhost', 27017)

        db = client["mydb"]
        collection = db['aws_prices']

        collection.insert_one(data)
        client.close()

if __name__ == "__main__":
    retriever = AWSPriceRetriever()
    print(retriever.get_current_prices())
