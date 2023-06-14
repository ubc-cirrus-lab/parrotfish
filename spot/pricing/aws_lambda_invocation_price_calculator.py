import decimal

from .invocation_price_calculator import InvocationPriceCalculator
from .aws_price_unit_retriever import AWSPriceUnitRetriever
import boto3
import numpy as np


class AWSLambdaInvocationPriceCalculator(InvocationPriceCalculator):
    def __init__(self, aws_session: boto3.Session, function_name: str):
        super().__init__(AWSPriceUnitRetriever(aws_session, function_name))

    def calculate_price(self, memory_mb: int, duration):
        price_units = self.price_unit_retriever.get_pricing_units()  # fetch the pricing units
        allocated_memory = 1.0 / 1024 * memory_mb  # convert MB to GB
        request_compute_time = np.ceil(duration) * 0.001  # convert ms to seconds
        total_compute = allocated_memory * request_compute_time
        compute_charge = price_units.compute_price * total_compute
        return price_units.request_price + compute_charge
