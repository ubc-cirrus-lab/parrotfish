from abc import ABC, abstractmethod
from .price_unit_retriever import PriceUnitRetriever


class InvocationPriceCalculator(ABC):
    def __init__(self, price_unit_retriever: PriceUnitRetriever):
        self.price_unit_retriever = price_unit_retriever

    @abstractmethod
    def calculate_price(self, memory_mb: int, duration):
        pass
