import unittest
import os

from spot.benchmark_config import BenchmarkConfig
from spot.definitions import ROOT_DIR

class TestConfigFile(unittest.TestCase):
    
    def setUp(self) -> None:
        self.config = BenchmarkConfig()
        self.config._set_properties('aws_func2', 'aws', 'us-west-1', 128, {'wow': 'woah'})

    def test_serialize(self):
        serial = self.config.serialize()
        print(serial)
        expected = """
        {
            "function_name": "aws_func2",
            "mem_size": 128,
            "region": "us-west-1",
            "vendor": "aws",
            "workload": {
                "wow": "woah"
            }
        }
        """
        assert ''.join(expected.split()) == ''.join(serial.split())

    def test_deserialize(self):
        with open(os.path.join(ROOT_DIR, "..", "tests/config_tests/sample_benchmark_config.json")) as f:
            self.config.deserialize(f)

        assert self.config.function_name == "AWSHelloWorld"
        assert self.config.region == "us-east-2"

