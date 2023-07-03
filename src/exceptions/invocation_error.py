from .exploration_error import ExplorationError


class InvocationError(ExplorationError):
    def __init__(self, msg: str, duration_ms: int = None):
        super().__init__(msg)
        self.duration_ms = duration_ms
