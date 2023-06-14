import decimal


class PricingUnits:
    def __init__(self, compute_price: float, request_price: float):
        self.compute_price = compute_price
        self.request_price = request_price

    def __str__(self):
        return f"Compute price: {self.compute_price}\n" \
               f"Request price: {self.request_price}"
