import unittest
import json

from black import assert_equivalent
import spot

from unittest.mock import patch, call

from spot.prices.aws_price_retriever import AWSPriceRetriever
from spot.db.db import DBClient

REQ_PRICE = 0.0000002
DURATION_PRICE = 0.00001667


class TestPriceRetrieval(unittest.TestCase):
    @patch.object(
        spot.prices.aws_price_retriever.DBClient,
        "add_document_to_collection_if_not_exists",
    )
    def test_fetch_current_pricing(self, mockDBAdd):
        priceRetriever = AWSPriceRetriever("test", 3000, "us-east-2")
        price = priceRetriever.fetch_current_pricing()
        self.assertEqual(REQ_PRICE, price["request_price"])
        self.assertEqual(round(DURATION_PRICE, 8), round(price['duration_price'], 8))
