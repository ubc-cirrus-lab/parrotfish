from abc import ABC, abstractmethod


class InvocationPriceCalculator(ABC):
    def __init__(self, function_name):
        self.function_name = function_name

    @abstractmethod
    def calculate_price(self, memory_mb: int, duration_ms) -> float:
        pass
