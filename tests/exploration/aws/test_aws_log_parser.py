import pytest

from src.exploration.aws.aws_log_parser import *
from src.exceptions import *


@pytest.fixture
def log_parser() -> AWSLogParser:
    return AWSLogParser()


class TestAWSLogParser:
    def test_log_parsing(self, log_parser):
        result_log = (
            "b'START RequestId: 03d92713-a4b2-4b07-a07a-653087817262 "
            "Version: $LATEST\\n"
            "END RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\n"
            "REPORT RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\"
            "tDuration: 18179.84 ms\\"
            "tBilled Duration: 18180 ms\\"
            "tMemory Size: 512 MB\\"
            "tMax Memory Used: 506 MB\\t\\n'"
        )
        expected = {"Duration": 18179.84, "Billed Duration": 18180.0, "Max Memory Used": 506.0, "Memory Size": 512.0}

        result = log_parser.parse_log(result_log)

        assert result == expected

    def test_lambda_timeout_error(self, log_parser):
        result_log = "Task timed out after"

        with pytest.raises(FunctionTimeoutError) as e:
            log_parser.parse_log(result_log)
        assert e.type == FunctionTimeoutError

    def test_lambda_enomem(self, log_parser):
        result_log = "errorType ENOMEM"

        with pytest.raises(FunctionENOMEM) as e:
            log_parser.parse_log(result_log)
        assert e.type == FunctionENOMEM

    def test_lambda_invocation_error(self, log_parser):
        result_log = "[ERROR] lambda function raises an error END RequestId."

        with pytest.raises(ExplorationError) as e:
            log_parser.parse_log(result_log)
        assert e.type == ExplorationError
