import re

from src.exceptions import *
from src.invocation.log_parser import LogParser


class AWSLogParser(LogParser):
    """Implementation of the LogParser for AWS Lambda functions."""

    def __init__(self):
        super().__init__(["Duration", "Billed Duration", "Max Memory Used", "Memory Size"])

    def parse_log(self, log: str) -> dict:
        """Parsing @log and returning a dictionary with values of each keyword in the attribute @log_parsing_keys.

        Args:
            log (str): Lambda function invocation's response log to parse.

        Returns:
            dict: parsed response log.

        Raises:
            FunctionTimeoutError: If the serverless function's execution time bypasses the configured time limit.
            FunctionENOMEM: If the serverless function's configured memory is not enough for lambda function's execution.
            InvocationError: If the serverless function raises an exception.
        """

        # check for timeout
        if "Task timed out after" in log:
            raise FunctionTimeoutError

        # check for ENOMEM
        if "ENOMEM" in log and "errorType" in log:
            raise FunctionENOMEM

        # check for errors
        error_msg = re.match(r".*\[ERROR\] (?P<error>.*)END RequestId.*", log)
        if error_msg is not None:
            raise InvocationError(error_msg["error"])

        # parse the log keys and prepare result.
        res = {}
        for key in self.log_parsing_keys:
            m = re.match(rf".*\\t{key}: (?P<value>[0-9.]+) (ms|MB).*", log)
            res[key] = float(m["value"])
        return res
