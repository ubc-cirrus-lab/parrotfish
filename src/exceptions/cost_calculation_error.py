from .exploration_error import ExplorationError


class CostCalculationError(ExplorationError):
    def __init__(self, msg: str):
        super().__init__(msg)
