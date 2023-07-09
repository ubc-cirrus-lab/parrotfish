import pytest

from src.exceptions import *
from src.exploration.gcp.gcp_log_parser import GCPLogParser


@pytest.fixture
def log_parser():
    return GCPLogParser()


class TestParseLog:
    def test_function_enomem(self, log_parser):
        result_log = "execid:Function execution took 50 ms, finished with status: 'error'"

        try:
            log_parser.parse_log(result_log)
        except FunctionENOMEM as e:
            assert e.duration_ms == 50

        with pytest.raises(FunctionENOMEM) as e:
            log_parser.parse_log(result_log)
        assert e.type == FunctionENOMEM

    def test_function_invocation_error(self, log_parser):
        result_log = "execid:Function execution took 50 ms, finished with status: 'crash'"

        try:
            log_parser.parse_log(result_log)
        except InvocationError as e:
            assert e.duration_ms == 50

        with pytest.raises(InvocationError) as e:
            log_parser.parse_log(result_log)
        assert e.type == InvocationError

    def test_log_parsing_error(self, log_parser):
        result_log = "not a valid log"

        with pytest.raises(LogParsingError) as e:
            log_parser.parse_log(result_log)
        assert e.type == LogParsingError
