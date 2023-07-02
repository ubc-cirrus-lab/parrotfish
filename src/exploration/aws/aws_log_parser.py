import logging
import re

from src.exceptions import *
from src.exploration.log_parser import LogParser


class AWSLogParser(LogParser):
    """Implementation of the LogParser for AWS Lambda functions."""

    def __init__(self):
        super().__init__(["Duration", "Billed Duration", "Max Memory Used", "Memory Size"])
        self._logger = logging.getLogger(__name__)

    def parse_log(self, log: str) -> int:
        """Parsing @log and returning a dictionary with values of each keyword in the attribute @log_parsing_keys.

        Args:
            log (str): Lambda function exploration's response log to parse.

        Returns:
            int: Billed duration of the lambda function's exploration.

        Raises:
            FunctionENOMEM: If the serverless function's configured memory is not enough for lambda function's execution.
            InvocationError: If the serverless function raises an exception.
        """
        # parse the log keys and prepare result.
        results = {}
        for key in self.log_parsing_keys:
            m = re.match(rf".*\\t{key}: (?P<value>[0-9.]+) (ms|MB).*", log)
            results[key] = float(m["value"])

        self._logger.info(results)

        # check for timeout
        if "Task timed out after" in log:
            raise FunctionENOMEM("Serverless function time out error. The execution time limit is reached.")

        # check for ENOMEM
        if results["Max Memory Used"] >= results["Memory Size"]:
            raise FunctionENOMEM

        # check for errors
        error_msg = re.match(r".*\[ERROR\] (?P<error>.*)END RequestId.*", log)
        if error_msg is not None:
            raise InvocationError(error_msg["error"])

        return int(results["Billed Duration"])
