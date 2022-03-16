from spot.prices.price_retriever import PriceRetriever
import time as time

from spot.db.db import DBClient
from spot.constants import *


class AWSPriceRetriever(PriceRetriever):
    def __init__(self, db: DBClient, region):
        super().__init__()
        self.DBClient = db
        self.region = region

    def fetch_current_pricing(self) -> dict:
        current_pricing = {}

        parameters = {
            "vendor": "aws",
            "service": "AWSLambda",
            "family": "Serverless",
            "region": self.region,
            "type": "AWS-Lambda-Requests",
            "purchaseOption": "on_demand",
        }
        request_price = self._current_price(parameters)
        current_pricing[REQUEST_PRICE] = request_price
        parameters["type"] = "AWS-Lambda-Duration"
        duration_price = self._current_price(parameters)
        current_pricing[DURATION_PRICE] = duration_price
        current_pricing[TIMESTAMP] = int(time.time() * 100)
        current_pricing[REGION] = self.region

        self.DBClient.add_document_to_collection_if_not_exists(
            DB_NAME_PRICING,
            "AWS",
            current_pricing,
            {
                REQUEST_PRICE: request_price,
                DURATION_PRICE: duration_price,
                REGION: self.region,
            },
        )
        return current_pricing


"""
a = AWSPriceRetriever("localhost", 27017)
a.fetch_current_pricing()
"""
