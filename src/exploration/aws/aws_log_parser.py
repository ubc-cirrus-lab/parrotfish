import logging
import re

from src.exceptions import *
from src.exploration.log_parser import LogParser


class AWSLogParser(LogParser):
    def __init__(self):
        super().__init__(["Duration", "Billed Duration", "Max Memory Used", "Memory Size"])
        self._logger = logging.getLogger(__name__)

    def parse_log(self, log: str) -> int:
        # parse the log keys and prepare result.
        results = {}
        for key in self.log_parsing_keys:
            m = re.match(rf".*\\t{key}: (?P<value>[0-9.]+) (ms|MB).*", log)
            results[key] = float(m["value"])
        billed_duration = int(results["Billed Duration"])

        # log the parsed response in DEBUG mode.
        self._logger.debug(results)

        # check for timeout
        if "Task timed out after" in log:
            raise FunctionTimeoutError(duration_ms=billed_duration)

        # check for ENOMEM
        if results["Max Memory Used"] >= results["Memory Size"]:
            raise FunctionENOMEM(duration_ms=billed_duration)

        # check for errors
        error_msg = re.match(r".*\[ERROR\] (?P<error>.*)END RequestId.*", log)
        if error_msg is not None:
            raise InvocationError(error_msg["error"], billed_duration)

        return billed_duration
