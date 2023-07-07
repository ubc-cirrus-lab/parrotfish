from abc import ABC, abstractmethod


class LogParser(ABC):
    """This class provides the operation for parsing the serverless function invocation's response log."""

    def __init__(self, log_parsing_keys: list):
        self.log_parsing_keys = log_parsing_keys

    @abstractmethod
    def parse_log(self, log: str) -> int:
        """Parses invocation's response log and returns the billed duration in ms.

        Args:
            log (str): Serverless function exploration's response log to parse.

        Returns:
            int: Billed duration of the serverless function's exploration.

        Raises:
            FunctionTimeoutError: If the serverless function's execution reached the timeout.
            FunctionENOMEM: If the serverless function's configured memory is not enough for lambda function's execution.
            InvocationError: If the serverless function's invocation raises an exception.
        """
        pass
