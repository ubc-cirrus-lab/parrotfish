from spot.prices.price_retriever import PriceRetriever
import time

from spot.context import Context
from spot.constants import *


class AWSPriceRetriever(PriceRetriever):
    def __init__(self, ctx: Context, region):
        super().__init__()
        self.ctx = ctx
        self.region = region

    def fetch_current_pricing(self) -> dict:
        parameters = {
            "vendor": "aws",
            "service": "AWSLambda",
            "family": "Serverless",
            "region": self.region,
            "type": "AWS-Lambda-Duration",
            "purchaseOption": "on_demand",
        }
        request_price = self._current_price(parameters)
        duration_price = self._current_price(parameters)
        current_pricing = {
            "provider": "AWS",
            REQUEST_PRICE: request_price,
            DURATION_PRICE: duration_price,
            TIMESTAMP: int(time.time() * 1000),
            REGION: self.region
        }
        self.ctx.record_pricing(
            current_pricing,
        )
        return current_pricing
