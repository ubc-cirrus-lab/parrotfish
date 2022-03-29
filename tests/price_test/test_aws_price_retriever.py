import unittest
import unittest.mock as mock
import json

import spot

from spot.prices.aws_price_retriever import AWSPriceRetriever

REQ_PRICE = 0.0000002
DURATION_PRICE = 0.00001667


class TestPriceRetrieval(unittest.TestCase):
    def test_fetch_current_pricing(self):
        priceRetriever = AWSPriceRetriever(mock.Mock(), "us-east-2")
        price = priceRetriever.fetch_current_pricing()
        self.assertEqual(REQ_PRICE, price["request_price"])
        self.assertEqual(round(DURATION_PRICE, 8), round(price["duration_price"], 8))
