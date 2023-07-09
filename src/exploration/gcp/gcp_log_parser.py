import re

from src.exceptions import LogParsingError, FunctionENOMEM, InvocationError
from src.exploration.log_parser import LogParser


class GCPLogParser(LogParser):
    def __init__(self):
        super().__init__(['Function execution took', 'finished with status'])

    def parse_log(self, log: str) -> int:
        pattern = re.compile(rf"(\w+):{self.log_parsing_keys[0]} (\d+) ms, {self.log_parsing_keys[1]}.*: (.*)")
        m = pattern.search(log)
        if m is None:
            raise LogParsingError
        execution_id = m.group(1)
        billed_duration = int(m.group(2))
        status = m.group(3)

        if status == "'error'":
            raise FunctionENOMEM(duration_ms=billed_duration)

        if status == "'crash'":
            raise InvocationError(f"Function raises an exception. Please check the logs associated with the execution "
                                  f"id: {execution_id} to debug your function.", duration_ms=billed_duration)

        return billed_duration
