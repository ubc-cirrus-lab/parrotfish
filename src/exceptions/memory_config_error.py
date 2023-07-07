from .exploration_error import ExplorationError


class MemoryConfigError(ExplorationError):
    def __init__(self, msg):
        super().__init__(msg)
