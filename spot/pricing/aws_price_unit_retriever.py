import decimal
import boto3
import json

from ..pricing import *
from ..data_model import *


class AWSPriceUnitRetriever(PriceUnitRetriever):
    """Implementation of the PriceUnitRetriever for AWS Lambda functions.

    This class provides the operation to determine the pricing units of a given lambda function.
    """
    def __init__(self, aws_session: boto3.Session, function_name: str):
        super().__init__(function_name)
        self.aws_session = aws_session

    def get_pricing_units(self) -> PricingUnits:
        """For a given function we fetch the configuration, determine the underlying architecture and fetch pricing
        information and parse it accordingly to determine the pricing units.
        """
        response = self.aws_session.client('pricing').get_products(
            ServiceCode='AWSLambda',
            Filters=[
                {
                    'Type': 'TERM_MATCH',
                    'Field': 'regionCode',
                    'Value': self.aws_session.region_name
                },
            ]
        )

        # Parsing the pricing information
        pricing = {}
        for price in response['PriceList']:

            price_group = json.loads(price)["product"]["attributes"]["group"]
            price_dimensions = list(json.loads(price)["terms"]["OnDemand"].values())[0]['priceDimensions']

            if price_group == "AWS-Lambda-Duration-ARM":
                pricing["Execution time price ARM"] = max(
                    [float(list(price_dimensions.values())[i]['pricePerUnit']['USD']) for i in
                     range(len(price_dimensions))])
            elif price_group == "AWS-Lambda-Duration":
                pricing["Execution time price"] = max(
                    [float(list(price_dimensions.values())[i]['pricePerUnit']['USD']) for i in
                     range(len(price_dimensions))])
            elif price_group == "AWS-Lambda-Requests-ARM":
                pricing["Request price ARM"] = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
            elif price_group == "AWS-Lambda-Requests":
                pricing["Request price"] = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])

        # Determine the underlying architecture and return the pricing units accordingly
        architecture = self.aws_session.client('lambda').get_function_configuration(FunctionName=self.function_name)['Architectures'][0]

        if architecture == 'arm64':
            return PricingUnits(pricing["Execution time price ARM"], pricing["Request price ARM"])

        return PricingUnits(pricing["Execution time price"], pricing["Request price"])
