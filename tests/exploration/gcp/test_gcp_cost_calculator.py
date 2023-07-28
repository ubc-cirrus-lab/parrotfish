from unittest import mock

import pytest
from google.api_core.exceptions import GoogleAPICallError

from src.exception import CostCalculationError
from src.exploration.gcp.gcp_cost_calculator import GCPCostCalculator


@pytest.fixture
def calculator() -> GCPCostCalculator:
    return GCPCostCalculator("example_function", "us-east1")


class TestGetProductName:
    def test_nominal_case(self, calculator):
        # Arrange
        product = type("", (), {})()
        product.display_name = "Cloud Functions"
        expected_product_name = "service-name"
        product.name = expected_product_name
        calculator.client.list_services = mock.Mock(return_value=[product])

        # Action
        product_name = calculator._get_product_name()

        # Assert
        assert product_name == expected_product_name

    def test_google_api_call_error(self, calculator):
        calculator.client.list_services = mock.Mock(
            side_effect=GoogleAPICallError("error")
        )

        with pytest.raises(CostCalculationError) as e:
            calculator._get_product_name()
        assert e.type == CostCalculationError


class TestGetPricingUnits:
    @mock.patch("src.exploration.gcp.gcp_cost_calculator.billing")
    def test_nominal_case(self, billing, calculator):
        # Arrange
        calculator._get_product_name = mock.Mock(return_value="product_name")
        billing.ListSkusRequest = mock.Mock()
        product1 = type("", (), {})()
        product1.service_regions = ["us-east1"]
        product1.description = "Memory Time"
        product2 = type("", (), {})()
        product2.service_regions = ["us-east1"]
        product2.description = "CPU Time"
        price = type("", (), {})()
        price.pricing_expression = type("", (), {})()
        tier = type("", (), {})()
        tier.unit_price = type("", (), {})()
        tier.unit_price.units = 0
        tier.unit_price.nanos = 4 * 10**7
        price.pricing_expression.tiered_rates = [tier]
        product1.pricing_info = [price]
        product2.pricing_info = [price]
        calculator.client.list_skus = mock.Mock(return_value=[product1, product2])

        # Action
        pricing_units = calculator._get_pricing_units()

        # Assert
        assert pricing_units == {"memory": 0.04, "cpu": 0.04}

    def test_index_error(self, calculator):
        calculator._get_product_name = mock.Mock(return_value="product_name")
        calculator.client.list_skus = mock.Mock(return_value=[])

        with pytest.raises(CostCalculationError) as e:
            calculator._get_pricing_units()
        assert e.type == CostCalculationError


class TestCalculatePrice:
    def test_nominal_case(self, calculator):
        # Arrange
        calculator.pricing_units = {"memory": 0.02, "cpu": 0.02, "request": 0.01}

        # Action
        price = calculator.calculate_price(128, 300)

        # Assert
        assert price == 0.01195
