from abc import ABC, abstractmethod


class LogParser(ABC):
    """This is an abstract class to parse serverless function's response log.

    This class is to be implemented for every cloud provider.
    """

    def __init__(self, log_parsing_keys: list):
        self.log_parsing_keys = log_parsing_keys

    @abstractmethod
    def parse_log(self, log: str) -> int:
        """Parsing @log and returning a dictionary with values of each keyword in the attribute @log_parsing_keys.

        Args:
            log (str): Serverless function exploration's response log to parse.

        Returns:
            int: Billed duration of the serverless function's exploration.

        Raises:
            FunctionENOMEM: If the serverless function's configured memory is not enough for lambda function's execution.
            InvocationError: If the serverless function raises an exception.
        """
        pass
