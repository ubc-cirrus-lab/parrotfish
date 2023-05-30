from spot.logs import *
from spot.exceptions import *
import unittest


class TestAWSLogParser(unittest.TestCase):
    def setUp(self) -> None:
        self.log_parser = AWSLogParser()
        self.keys = ["Duration", "Billed Duration", "Max Memory Used", "Memory Size"]

    def test_log_parsing(self):
        string_to_parse = (
            "b'START RequestId: 03d92713-a4b2-4b07-a07a-653087817262 "
            "Version: $LATEST\\n"
            "END RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\n"
            "REPORT RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\"
            "tDuration: 18179.84 ms\\"
            "tBilled Duration: 18180 ms\\"
            "tMemory Size: 512 MB\\"
            "tMax Memory Used: 506 MB\\t\\n'"
        )
        res = self.log_parser.parse_log(string_to_parse, self.keys)
        self.assertDictEqual(
            {
                "Duration": 18179.84,
                "Billed Duration": 18180.0,
                "Max Memory Used": 506.0,
                "Memory Size": 512.0,
            },
            res,
        )

    def test_exception_LambdaTimeoutError(self):
        log = "Task timed out after"
        with self.assertRaises(LambdaTimeoutError):
            res = self.log_parser.parse_log(log, self.keys)

    def test_exception_LambdaENOMEM(self):
        log = "errorType ENOMEM"
        with self.assertRaises(LambdaENOMEM):
            res = self.log_parser.parse_log(log, self.keys)


if __name__ == "__main__":
    unittest.main()
