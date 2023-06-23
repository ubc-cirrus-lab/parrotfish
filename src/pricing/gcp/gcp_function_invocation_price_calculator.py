import numpy as np

from ..invocation_price_calculator import InvocationPriceCalculator
from src.data_model import *


class GCPFunctionInvocationPriceCalculator(InvocationPriceCalculator):
    def __init__(self, function_name):
        super().__init__(function_name)

    def calculate_price(self, memory_mb: int, duration: float):
        """GCP offers a consumption-based pricing model for its serverless compute platform, Cloud Functions. The pricing factors for Cloud Functions include the following:

        Compute Time: The time taken to execute the function, measured in gigabyte-seconds (GB-seconds) and billed per millisecond.
        Memory Usage: The amount of memory allocated to the function during execution, measured in gigabytes (GB) and billed per gigabyte-second.
        Invocations: The number of times a function is triggered or called.
        Network Egress: Data sent from the function to external networks.
        """
        price_units = (
            self.get_pricing_units()
        )  # fetch the pricing units
        allocated_memory = 1.0 / 1024 * memory_mb  # convert MB to GB
        request_compute_time = np.ceil(duration) * 0.001  # convert ms to seconds
        total_compute = allocated_memory * request_compute_time
        compute_charge = price_units.compute_price * total_compute
        return price_units.request_price + compute_charge

    def get_pricing_units(self) -> PricingUnits:
        pass
