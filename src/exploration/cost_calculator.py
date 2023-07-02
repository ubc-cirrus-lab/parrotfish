from abc import ABC, abstractmethod

import numpy as np


class CostCalculator(ABC):
    def __init__(self, function_name):
        self.function_name = function_name

    @abstractmethod
    def calculate_price(self, memory_mb: int, duration_ms: float or np.ndarray) -> float or np.ndarray:
        """Retrieving the serverless function pricing units, and calculate the exploration price based on the memory and
        execution time.

        Args:
            memory_mb (int): configured memory value in MB.
            duration_ms (float or np.ndarray): one or multiple invocations' execution time in Ms.

        Return:
            float or np.ndarray: the exploration's price or prices in USD.

        Raises:
            TypeError: if the arguments' types are not compatible.
            CostCalculationError: If exploration's price calculation fails.
        """
        pass
