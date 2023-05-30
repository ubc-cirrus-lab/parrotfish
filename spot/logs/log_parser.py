from abc import ABC, abstractmethod


class LogParser(ABC):
    """This is an abstract class to parse logs.

    This class provides a basic interface to parse logs returned once we invoke a serverless function.
    This class is to be implemented for every cloud provider.
    """
    def __int__(self):
        pass

    @abstractmethod
    def parse_log(self, log: str, keys: list) -> dict:
        """Parsing the log and returning a dictionary with values of each keyword in keys.

        Args:
            log: the log string to parse.
            keys: a list of all the keywords we want to parse from the log.
        Some exceptions could be raised while parsing the logs.
        """
        pass
