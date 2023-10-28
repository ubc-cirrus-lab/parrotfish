from unittest import mock
from unittest.mock import patch

import pytest

from src.exception import *
from src.exploration.aws.aws_cost_calculator import AWSCostCalculator


@pytest.fixture
def calculator_with_mock_aws_session() -> AWSCostCalculator:
    # Mock the AWS session and client objects.
    mock_aws_session = mock.Mock()

    # Configure the mock objects to return the expected values.
    mock_aws_session.client.return_value = mock.Mock()

    # Create an instance of the AWSCostCalculator.
    return AWSCostCalculator("example_function", mock_aws_session)


class TestGetPricingUnits:
    def test_get_pricing_units(self, calculator_with_mock_aws_session):
        # Mock the response for get_products() from pricing client
        boto3_client_mock = mock.Mock()
        with patch('boto3.client', return_value=boto3_client_mock):
            boto3_client_mock.get_products.return_value = {
                "PriceList": [
                    '{"product": {"attributes": {"group": "AWS-Lambda-Duration-ARM"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": "0.0000150000"}}}}}}}',
                    '{"product": {"attributes": {"group": "AWS-Lambda-Duration"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": "0.0000166667"}}}}}}}',
                    '{"product": {"attributes": {"group": "AWS-Lambda-Requests-ARM"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": "0.0000002000"}}}}}}}',
                    '{"product": {"attributes": {"group": "AWS-Lambda-Requests"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": "0.0000002000"}}}}}}}',
                ]
            }

        # Mock the response for get_function_configuration() from lambda client
        calculator_with_mock_aws_session.aws_session.client(
            "lambda"
        ).get_function_configuration.return_value = {"Architectures": ["x86"]}

        # Call the _get_pricing_units() method
        pricing_units = calculator_with_mock_aws_session._get_pricing_units()

        # Perform the assertion
        assert pricing_units == {"compute": 0.0000166667, "request": 0.0000002}

    def test_get_pricing_units_index_error(self, calculator_with_mock_aws_session):
        # Mock the response for get_products() from pricing client
        calculator_with_mock_aws_session.aws_session.client(
            "pricing"
        ).get_products.return_value = {
            "PriceList": [
                '{"product": {"attributes": {"group": "AWS-Lambda-Duration-ARM"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": }}}}}}',
            ]
        }

        # Mock the response for get_function_configuration() from lambda client
        calculator_with_mock_aws_session.aws_session.client(
            "lambda"
        ).get_function_configuration.return_value = {"Architectures": ["x86"]}

        with pytest.raises(CostCalculationError) as e:
            # Response parsing fails.
            calculator_with_mock_aws_session._get_pricing_units()

        assert e.type == CostCalculationError


class TestCalculator:
    @pytest.fixture
    def calculator_with_mock_get_pricing_units(
        self, calculator_with_mock_aws_session
    ) -> AWSCostCalculator:
        calculator_with_mock_aws_session.pricing_units = {
            "compute": 0.0000166667,
            "request": 0.0000002,
        }
        return calculator_with_mock_aws_session

    def test_calculate_price_one_invocation(
        self, calculator_with_mock_get_pricing_units
    ):
        assert (
            calculator_with_mock_get_pricing_units.calculate_price(128, 300)
            == 8.2500125e-07
        )

    def test_calculate_price_multiple_invocations(
        self, calculator_with_mock_get_pricing_units
    ):
        computed_invocations_prices = (
            calculator_with_mock_get_pricing_units.calculate_price(128, [300, 500])
        )
        expected_invocations_prices = [8.2500125e-07, 1.24166875e-06]

        assert len(computed_invocations_prices) == len(expected_invocations_prices)
        assert all(
            [
                a == b
                for a, b in zip(
                    computed_invocations_prices, expected_invocations_prices
                )
            ]
        )

    @pytest.mark.parametrize("memory_mb, duration_ms", [("memory", 300), (300, "time")])
    def test_type_error(
        self, memory_mb, duration_ms, calculator_with_mock_get_pricing_units
    ):
        with pytest.raises(TypeError) as e:
            calculator_with_mock_get_pricing_units.calculate_price(
                memory_mb, duration_ms
            )

        assert e.type == TypeError
