from spot.prices.price_retriever import PriceRetriever
import os
import json
from pymongo import MongoClient
import time as time

class AWSPriceRetriever(PriceRetriever):
    def __init__(self):
        super().__init__()

    def fetch_current_pricing(self, region="us-east-1") -> dict:
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
