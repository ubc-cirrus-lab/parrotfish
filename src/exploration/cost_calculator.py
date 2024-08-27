from abc import ABC, abstractmethod

import numpy as np

from typing import Union

class CostCalculator(ABC):
    def __init__(self, function_name):
        self.function_name = function_name
        self.pricing_units = None

    @abstractmethod
    def calculate_price(
        self, memory_mb: int, duration_ms: Union[float, np.ndarray], cpu: float = None
    ) -> Union[float, np.ndarray]:
        """Calculates the exploration price based on the memory and execution time.

        Args:
            memory_mb (int): configured memory value in MB.
            duration_ms (float or np.ndarray): one or multiple invocations' execution time in ms.

        Return:
            float or np.ndarray: Exploration's price or prices in USD.

        Raises:
            TypeError: If the arguments' types are not compatible.
            CostCalculationError: If exploration's price calculation fails.
        """
        pass
