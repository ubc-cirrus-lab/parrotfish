import requests
import re
import os
import json
import datetime
from spot.constants import ROOT_DIR

API_URL = "https://pricing.api.infracost.io/graphql"
API_KEY_DIR = os.path.join(ROOT_DIR, "prices/credentials.yml")
CACHE_INVALID_DAYS = 1.0


class PriceNotFoundException(Exception):
    pass


class PriceRetriever:
    def __init__(self):
        self._key = ""
        self._key = self._read_api_key()

    def _current_price(self, parameters):
        price = self._fetch_price(parameters)
        return price

    def _fetch_price(self, parameters: dict) -> float:
        query = """query {{
        products(
          filter: {{
            vendorName: "{vendor}",
            service: "{service}",
            productFamily: "{family}",
            region: "{region}",
            attributeFilters: [
                {{ key: "group", value: "{type}" }}
            ]
            
          }},
          
        ) {{
        prices(
        filter: {{purchaseOption: "{purchaseOption}" }}
        ) {{
            USD
          }}
         }}
       }}""".format(
            **parameters
        )
        url = API_URL
        r = requests.post(url, json={"query": query}, headers={"X-Api-Key": self._key})
        if r.status_code != 200:
            print(f"POST Request failed with status code {r.status_code}")
            raise PriceNotFoundException
        result_json = r.json()
        try:
            price = float(result_json["data"]["products"][0]["prices"][0]["USD"])
        except:
            raise PriceNotFoundException
        return price

    def _read_api_key(self) -> str:
        try:
            with open(API_KEY_DIR, "r") as file:
                for line in file.readlines():
                    match = re.search(r"api_key: (.*)", line)
                    if match:
                        return match.group(1)
                print(
                    "Could not find the API key in the '~/.config/infracost/credentials.yml' file"
                )
        except FileNotFoundError:
            print(
                "Could not find Infracost Cloud Pricing API key. Run 'infracost register' to generate a key"
            )
        return ""
