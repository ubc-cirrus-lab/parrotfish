from spot.exceptions import *
from .log_parser import LogParser
import re


class AWSLogParser(LogParser):
    """Implementation of the LogParser for AWS Lambda functions.

    This class provides parsing operations on the log retrieved after invoking the lambda function.
    """

    def __init__(self):
        super().__init__(
            ["Duration", "Billed Duration", "Max Memory Used", "Memory Size"]
        )

    def parse_log(self, log: str) -> dict:
        """Parsing the logs_parsing retrieved once we invoke the lambda function.

        This method checks for timeout, ENOMEM and other errors from the log and if found raises appropriate exceptions.
        Args:
            log: the log string to parse.
        """

        # check for timeout
        if "Task timed out after" in log:
            raise LambdaTimeoutError

        # check for ENOMEM
        if "ENOMEM" in log and "errorType" in log:
            raise LambdaENOMEM

        # check for errors
        m = re.match(r".*\[ERROR\] (?P<error>.*)END RequestId.*", log)
        if m is not None:
            raise SingleInvocationError(m["error"])

        # parse the log keys and prepare result.
        res = {}
        for key in self.log_parsing_keys:
            m = re.match(rf".*\\t{key}: (?P<value>[0-9.]+) (ms|MB).*", log)
            res[key] = float(m["value"])
        return res
