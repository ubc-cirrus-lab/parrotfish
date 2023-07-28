import numpy as np
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import billing
from google.type.money_pb2 import Money

from src.exception import CostCalculationError
from src.exploration.cost_calculator import CostCalculator


class GCPCostCalculator(CostCalculator):
    def __init__(self, function_name: str, region: str):
        super().__init__(function_name)
        self.region = region
        self.client = billing.CloudCatalogClient()

    def calculate_price(
        self, memory_mb: int, duration_ms: float or np.ndarray
    ) -> float or np.ndarray:
        # if pricing units cache is empty we should retrieve pricing units.
        if self.pricing_units is None:
            self.pricing_units = self._get_pricing_units()  # fetch the pricing units
            # The invocation's request price is not provided by the GCP Billing API.
            self.pricing_units["request"] = 4 * 10 ** (-7)

        cpu_usage_mhz = (
            memory_mb / 128
        ) * 200  # The CPU usage in Mhz, this is proportional to the memory config

        allocated_memory = 1.0 / 1024 * memory_mb  # convert MB to GB
        allocated_cpu = cpu_usage_mhz / 1000  # convert Mhz to Ghz
        request_compute_time = (
            np.ceil(duration_ms / 100) * 0.1
        )  # convert ms to seconds 100 ms increments

        memory_total_compute = allocated_memory * request_compute_time
        memory_compute_charge = self.pricing_units["memory"] * memory_total_compute

        cpu_total_compute = allocated_cpu * request_compute_time
        cpu_compute_charge = self.pricing_units["cpu"] * cpu_total_compute

        return (
            self.pricing_units["request"] + memory_compute_charge + cpu_compute_charge
        )

    def _get_pricing_units(self) -> dict:
        """Fetches the pricing information from the GCP Cloud Billing API.
        Should enable the Cloud Billing API is required.

        Returns:
            dict: The pricing units retrieved.

        Raises:
            CostCalculationError: If an error occurred while trying to retrieve pricing units.
        """
        pricing_units = []
        product_name = self._get_product_name()

        if product_name is not None:
            # Initialize request argument(s)
            request = billing.ListSkusRequest(parent=product_name, currency_code="USD")

            # Make the request
            page_result = self.client.list_skus(request=request)

            # Handle the response
            for product in [
                result
                for result in page_result
                if self.region in result.service_regions
            ]:
                for description in ["Memory Time", "CPU Time"]:
                    if product.description == description:
                        for price in product.pricing_info:
                            for tier in price.pricing_expression.tiered_rates:
                                pricing_units.append(self._parse_money(tier.unit_price))

        try:
            return {"memory": pricing_units[0], "cpu": pricing_units[1]}
        except IndexError:
            raise CostCalculationError(
                "Parsing the prices retrieved from GCP Cloud Billing API failed."
            )

    def _get_product_name(self) -> str:
        """Retrieves the product name from the GCP Cloud Billing API."""
        try:
            products = self.client.list_services()
        except GoogleAPICallError as e:
            raise CostCalculationError(e.args[0])

        for product in products:
            if "Cloud Functions" in product.display_name:
                return product.name

    @staticmethod
    def _parse_money(money: Money) -> float:
        return money.units + money.nanos * 10 ** (-9)
