from spot.prices.price_retriever import PriceRetriever

class AWSPriceRetriever(PriceRetriever):
    def __init__(self):
        super().__init__()

    def get_current_prices(self, region="us-east-1") -> dict:
        """
        Returns the price per request and price per second as a dictionary

        Keyword arguments:
        Region -- the AWS region for pricing information (default "us-east-1")
        """
        parameters = {"vendor": "aws", "service": "AWSLambda", "family": "Serverless", "region": region, "type": "AWS-Lambda-Requests", "purchaseOption": "on_demand"}
        request_price = self._current_price(parameters)
        parameters["type"] = "AWS-Lambda-Duration"
        duration_price = self._current_price(parameters)
        return {"per_request": request_price, "per_gb_second": duration_price}

if __name__ == "__main__":
    retriever = AWSPriceRetriever()
    print(retriever.get_current_prices())
