from src.exceptions import ExplorationError


class LogParsingError(ExplorationError):
    def __init__(self):
        super().__init__("Error has been raised while parsing the logs.")
