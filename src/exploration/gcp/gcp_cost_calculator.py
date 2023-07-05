import numpy as np

from src.exploration.cost_calculator import CostCalculator


class GCPCostCalculator(CostCalculator):
    def __init__(self, function_name: str):
        super().__init__(function_name)

    def calculate_price(self, memory_mb: int, duration_ms: float or np.ndarray) -> float or np.ndarray:
        pass
