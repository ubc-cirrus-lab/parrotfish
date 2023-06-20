from unittest import mock
import pytest

from spot.pricing.aws import AWSLambdaInvocationPriceCalculator
from spot.data_model.pricing_units import PricingUnits


@pytest.fixture
def calculator():
    # Mock the necessary AWS session and client objects
    mock_aws_session = mock.Mock()

    # Configure the mock objects to return the expected values
    mock_aws_session.client.return_value = mock.Mock()

    # Create an instance of the AWSLambdaInvocationPriceCalculator
    return AWSLambdaInvocationPriceCalculator("pyaes", mock_aws_session)


def test_get_pricing_units(calculator):
    # Mock the response for get_products() from pricing client
    calculator.aws_session.client("pricing").get_products.return_value = {
        "PriceList": [
            '{"product": {"attributes": {"group": "AWS-Lambda-Duration-ARM"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": "0.0000150000"}}}}}}}',
            '{"product": {"attributes": {"group": "AWS-Lambda-Duration"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": "0.0000166667"}}}}}}}',
            '{"product": {"attributes": {"group": "AWS-Lambda-Requests-ARM"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": "0.0000002000"}}}}}}}',
            '{"product": {"attributes": {"group": "AWS-Lambda-Requests"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": "0.0000002000"}}}}}}}'
        ]
    }

    # Mock the response for get_function_configuration() from lambda client
    calculator.aws_session.client("lambda").get_function_configuration.return_value = {"Architectures": ["x86"]}

    # Call the _get_pricing_units() method
    pricing_units = calculator._get_pricing_units()

    # Perform the assertion
    assert pricing_units == PricingUnits(0.0000166667, 0.0000002)


def test_get_pricing_units_index_error(calculator):
    # Mock the response for get_products() from pricing client
    calculator.aws_session.client("pricing").get_products.return_value = {
        "PriceList": [
            '{"product": {"attributes": {"group": "AWS-Lambda-Duration-ARM"}, "terms": {"OnDemand": {"offerTermCode": "JRTCKXETXF", "priceDimensions": {"JRTCKXETXF.6YS6EN2CT7": {"pricePerUnit": {"USD": }}}}}}',
          ]
    }

    # Mock the response for get_function_configuration() from lambda client
    calculator.aws_session.client("lambda").get_function_configuration.return_value = {"Architectures": ["x86"]}

    with pytest.raises(IndexError) as e:
        # Response parsing fails.
        calculator._get_pricing_units()

    assert e.type == IndexError


def test_calculate_price(calculator):
    # Mock the response for _get_pricing_units()
    calculator._get_pricing_units = mock.Mock()
    calculator._get_pricing_units.return_value = PricingUnits(0.0000166667, 0.0000002)

    assert calculator.calculate_price(128, 300) == 8.2500125e-07
