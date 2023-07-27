from .optimization_error import OptimizationError


class SamplingError(OptimizationError):
    def __init__(self, msg: str):
        super().__init__(msg)
