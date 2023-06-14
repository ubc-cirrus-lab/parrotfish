from abc import ABC, abstractmethod


class LogParser(ABC):
    """This is an abstract class to parse logs_parsing.

    This class provides a basic interface to parse logs_parsing returned once we invoke a serverless function.
    This class is to be implemented for every cloud provider.
    """

    def __init__(self, log_parsing_keys: list):
        self.log_parsing_keys = log_parsing_keys

    @abstractmethod
    def parse_log(self, log: str) -> dict:
        """Parsing the log and returning a dictionary with values of each keyword in keys.

        Args:
            log: the log string to parse.
        Some exceptions could be raised while parsing the logs_parsing.
        """
        pass
