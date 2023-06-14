from ..data_model import PricingUnits
from abc import ABC, abstractmethod


class PriceUnitRetriever(ABC):
    """This is an interface to get the duration and the request pricing of a serverless functions.

    This class is to be implemented for every cloud provider.
    """
    def __init__(self, function_name):
        self.function_name = function_name

    @abstractmethod
    def get_pricing_units(self) -> PricingUnits:
        pass
