import unittest
import json
import requests_futures.sessions
from mock import patch
from unittest.mock import Mock

from spot.invocation.aws_function_invocator import AWSFunctionInvocator
from spot.invocation.iam_auth import IAMAuth

class TestInvocation(unittest.TestCase):

    def setUp(self):
        with open("tests/test_workload.json", "w+") as f:
            workload = json.dump(
                {
                    "test_name": "test_hello_world",
                    "test_duration_in_seconds": 5,
                    "random_seed": 100,
                    "blocking_cli": False,
                    "instances": {
                        "instance1": {
                            "application": "AWSHelloWorld",
                            "distribution": "Uniform",
                            "rate": 1,
                            "activity_window": [0, 1],
                            "payload": "tests/test_payload.json",
                            "host": "x8siu0es68.execute-api.us-east-2.amazonaws.com",
                            "stage": "default",
                            "resource": "AWSHelloWorld",
                        }
                    },
                },
                f,
            )

        with open("tests/test_payload.json", "w+") as f:

            payload = json.dump(
                {"key1": "poisson", "num_of_rows": 10, "num_of_cols": 10},
                f,
            )
        
        self.auth  = IAMAuth("x8siu0es68.execute-api.us-east-2.amazonaws.com", "default", "AWSHelloWorld")
    
    # @patch("spot.invocation.aws_function_invocator.FutureSession")
    def test_invoke(self):
        workload_path = "tests/test_workload.json"
        payload_path = "tests/test_payload.json"
        with open(payload_path, "r") as pl:
            payload = json.dumps(json.load(pl))

        ivk = AWSFunctionInvocator(workload_path, "AWSHelloWorld", 512, "us-east-2")
        ivk._invoke(self.auth, payload, [1])
        # self.assertTrue(mock_post.called)
        pass

