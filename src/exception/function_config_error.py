from .exploration_error import ExplorationError


class FunctionConfigError(ExplorationError):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Please make sure that the provided function name, configuration file and arguments are correct"
        super().__init__(msg)
