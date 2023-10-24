from src.exception import OptimizationError


class UnfeasibleConstraintError(OptimizationError):
    def __init__(self, msg: str = None):
        if not msg:
            msg = (
                "The constraint provided in the configuration file cannot be satisfied. Ignoring the constraint."
            )
        super().__init__(msg)
