from .exploration_error import ExplorationError


class InvocationError(ExplorationError):
    def __init__(self, msg):
        super().__init__(msg)
