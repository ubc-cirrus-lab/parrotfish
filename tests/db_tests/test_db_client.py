import unittest
import bson
from spot.db.db import DBClient


class TestDB(unittest.TestCase):
    def setUp(self) -> None:
        self.db = DBClient()

    def test_execute_max_value(self):
        max_timestamp = self.db.execute_max_value("AWSHelloWorld", "logs", "timestamp")
        assert type(max_timestamp) is bson.Int64
