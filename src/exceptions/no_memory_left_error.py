from src.exceptions import OptimizationError


class NoMemoryLeftError(OptimizationError):
    def __init__(self):
        super().__init__("No memory left in the memory space to explore with.")
