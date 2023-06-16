from dataclasses import dataclass


@dataclass
class PricingUnits:
    """Class for keeping track of the pricing units to calculate the serverless function invocation price."""
    compute_price: float
    request_price: float
