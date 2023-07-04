import pytest

from src.exceptions import *
from src.exploration.aws.aws_log_parser import *


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
        expected = 18180.0

        result = log_parser.parse_log(result_log)

        assert result == expected

    def test_lambda_timeout_error(self, log_parser):
        result_log = (
            "Task timed out after REPORT RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\tDuration: "
            "18179.84 ms\\tBilled Duration: 18180 ms\\tMemory Size: 512 MB\\tMax Memory Used: 506 MB\\t\\n'"
        )

        try:
            log_parser.parse_log(result_log)
        except FunctionTimeoutError as e:
            assert e.duration_ms == 18180

        with pytest.raises(FunctionTimeoutError) as e:
            log_parser.parse_log(result_log)
        assert e.type == FunctionTimeoutError

    def test_lambda_enomem(self, log_parser):
        result_log = (
            "REPORT RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\tDuration: 18179.84 ms\\tBilled "
            "Duration: 18180 ms\\tMemory Size: 512 MB\\tMax Memory Used: 512 MB\\t\\n'"
        )

        try:
            log_parser.parse_log(result_log)
        except FunctionENOMEM as e:
            assert e.duration_ms == 18180

        with pytest.raises(FunctionENOMEM) as e:
            log_parser.parse_log(result_log)
        assert e.type == FunctionENOMEM

    def test_lambda_invocation_error(self, log_parser):
        result_log = (
            "[ERROR] lambda function raises an error END RequestId. REPORT RequestId: "
            "03d92713-a4b2-4b07-a07a-653087817262\\tDuration: 18179.84 ms\\tBilled Duration: 18180 ms\\t"
            "Memory Size: 512 MB\\tMax Memory Used: 506 MB\\t\\n'"
        )

        try:
            log_parser.parse_log(result_log)
        except InvocationError as e:
            assert e.duration_ms == 18180

        with pytest.raises(InvocationError) as e:
            log_parser.parse_log(result_log)
        assert e.type == InvocationError
