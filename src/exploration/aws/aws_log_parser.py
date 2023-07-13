import logging
import math
import re

from src.exceptions import *
from src.exploration.log_parser import LogParser


class AWSLogParser(LogParser):
    def __init__(self):
        super().__init__(
            [
                "Duration",
                "Billed Duration",
                "Max Memory Used",
                "Memory Size",
                "Init Duration",
            ]
        )
        self._logger = logging.getLogger(__name__)

    def parse_log(self, log: str) -> int:
        # parse the log keys and prepare result.
        results = {}
        for key in self.log_parsing_keys:
            m = re.match(rf".*\\t{key}: (?P<value>[0-9.]+) (ms|MB).*", log)
            if m:
                results[key] = float(m["value"])

        if "Billed Duration" not in results:
            raise LogParsingError
        cold_start_time_ms = (
            0 if "Init Duration" not in results else results["Init Duration"]
        )
        execution_time_ms = int(results["Billed Duration"]) - math.ceil(
            cold_start_time_ms
        )

        # log the parsed response in DEBUG mode.
        self._logger.debug(results)

        # check for timeout
        if "Task timed out after" in log:
            raise FunctionTimeoutError(duration_ms=execution_time_ms)

        # check for ENOMEM
        if results["Max Memory Used"] >= results["Memory Size"]:
            raise FunctionENOMEM(duration_ms=execution_time_ms)

        # check for errors
        error_msg = re.match(r".*\[ERROR\] (?P<error>.*)END RequestId.*", log)
        if error_msg is not None:
            raise InvocationError(error_msg["error"], execution_time_ms)

        return execution_time_ms
