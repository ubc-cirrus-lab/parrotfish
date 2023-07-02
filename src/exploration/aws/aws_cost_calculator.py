import json
import re

import boto3
import numpy as np
from botocore.exceptions import ClientError

from src.data_model import *
from src.exceptions import *
from src.exploration.cost_calculator import CostCalculator


class AWSCostCalculator(CostCalculator):
    """A class for calculating the exploration price of an AWS Lambda function.

    This class inherits from `InvocationPriceCalculator` and provides methods to calculate the exploration price
    based on the underlying architecture, memory, and execution time of the Lambda function.
    """
    def __init__(self, function_name: str, aws_session: boto3.Session):
        super().__init__(function_name)
        self.aws_session = aws_session
        self.pricing_units = None

    def calculate_price(self, memory_mb: int, duration_ms: float or np.ndarray) -> float or np.ndarray:
        """Retrieving the AWS lambda pricing units, and calculate the exploration price based on the memory and
        execution time.

        Args:
            memory_mb (int): configured memory value in MB.
            duration_ms (float or np.ndarray): one or multiple invocations' execution time in Ms.

        Return:
            float or np.ndarray: Invocation's price or prices in USD.

        Raises:
            TypeError: If the arguments' types are not compatible.
            CostCalculationError: If exploration's price calculation fails.
        """
        # if pricing units cache is empty we should retrieve pricing units.
        if self.pricing_units is None:
            self.pricing_units = self._get_pricing_units()  # fetch the pricing units

        allocated_memory = 1.0 / 1024 * memory_mb  # convert MB to GB
        request_compute_time = np.ceil(duration_ms) * 0.001  # convert ms to seconds

        total_compute = allocated_memory * request_compute_time
        compute_charge = self.pricing_units.compute_price * total_compute

        return self.pricing_units.request_price + compute_charge

    def _get_pricing_units(self) -> PricingUnits:
        """For a given function we fetch the configuration, determine the underlying architecture and fetch pricing
        information and parse it accordingly to determine the pricing units.

        Returns:
            PricingUnits: The pricing units retrieved based on the lambda configuration.

        Raises:
            CostCalculationError: If an error occurred while trying to retrieve pricing units from aws.
        """
        try:
            response = self.aws_session.client("pricing").get_products(
                ServiceCode="AWSLambda",
                Filters=[
                    {
                        "Type": "TERM_MATCH",
                        "Field": "regionCode",
                        "Value": self.aws_session.region_name,
                    },
                ],
            )

            # Determine the underlying architecture and return the pricing units accordingly.
            architecture = self.aws_session.client("lambda").get_function_configuration(
                FunctionName=self.function_name
            )["Architectures"][0]

        except ClientError as e:
            raise CostCalculationError(e.args[0])

        else:
            # Create the filtering groups.
            price_groups = ["AWS-Lambda-Duration", "AWS-Lambda-Requests"]
            if architecture == "arm64":
                price_groups = ["AWS-Lambda-Duration-ARM", "AWS-Lambda-Requests-ARM"]

            # Parsing the pricing information.
            pricing = []
            for group in price_groups:
                # Loop over the price list and get the pricing units.
                for price in response['PriceList']:
                    # Filter by the group attribute.
                    if re.search(f'"group"\s*:\s*"{group}"', price):
                        # Get all match PricePerUnit.
                        all_match = re.findall('\{"USD"\s*:\s*"[.\d]*"}', price)
                        if all_match:
                            prices_per_tier = map(lambda element: float(json.loads(element)["USD"]), all_match)
                            pricing.append(max(prices_per_tier))
                            break

            try:
                return PricingUnits(pricing[0], pricing[1])
            except IndexError as e:
                raise CostCalculationError("Parsing the prices retrieved from AWS failed.")
