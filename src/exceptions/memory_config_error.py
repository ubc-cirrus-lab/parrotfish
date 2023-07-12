from .exploration_error import ExplorationError


class MemoryConfigError(ExplorationError):
    def __init__(self, msg=None):
        if msg is None:
            msg = (
                "Serverless function not found. Please make sure that the provided function name and configuration "
                "are correct!"
            )
        super().__init__(msg)
