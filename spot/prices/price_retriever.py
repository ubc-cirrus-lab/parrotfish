import requests
import re
import os
import json
import datetime

from spot.definitions import DATA_DIR

PRICES_FILE = "prices.json"
API_URL = "https://pricing.api.infracost.io/graphql"
API_KEY_DIR = ".config/infracost/credentials.yml"
CACHE_INVALID_DAYS = 1.0
PRICES_PATH = os.path.join(DATA_DIR, PRICES_FILE)

class PriceNotFoundException(Exception):
    pass

class PriceRetriever():
    def __init__(self):
        self._key = ''
        self._data = self._load_data()
        self._key = self._read_api_key()

    def get_current_prices(self, region="") -> dict:
        raise NotImplementedError

    def _current_price(self, parameters) -> float:
        """
        Returns the cached price if the fetch date is < 1 day old. Otherwise fetches the price from the API.
        If the fetch fails, then the outdated cached value will be returned with a warning.
        If both fetch and cache fail, then an exception will be raised
        """
        try:
            price_dict = self._get_price(parameters)
            delta = abs(datetime.datetime.fromisoformat(price_dict["timestamp"]) - datetime.datetime.now(datetime.timezone.utc))
            if (delta.days <= CACHE_INVALID_DAYS):
                price = price_dict["value"]
            else:
                try:
                    price = self._fetch_price(parameters)
                except:
                    print(f"Warning: Using a cached price that is older than the cache invalid range ({CACHE_INVALID_DAYS} days)")
                    price = price_dict["value"]
        except PriceNotFoundException:
            price = self._fetch_price(parameters)
        return price

    #Change this to db interaction instead of file saving
    def _load_data(self) -> dict:
        try:
            with open(PRICES_PATH, 'r') as file:
                return json.load(file)
        except:
            return {}

    def _save_data(self):
        with open(PRICES_PATH, 'w') as file:
            json.dump(self._data, file, indent=4)

    def _get_price(self, parameters : dict) -> dict:
        try:
            return self._data[parameters["vendor"]][parameters["service"]][parameters["region"]][parameters["type"]]
        except:
            raise PriceNotFoundException

    def _set_price(self, parameters : dict, price: float):
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if not parameters["vendor"] in self._data:
            self._data[parameters["vendor"]] = {parameters["service"]: {parameters["region"]: {parameters["type"]: {"value": price, "timestamp": timestamp}}}}
        elif not parameters["service"] in self._data[parameters["vendor"]]:
            self._data[parameters["vendor"]][parameters["service"]] = {parameters["region"]: {parameters["type"]: {"value": price, "timestamp": timestamp}}}
        elif not parameters["region"] in self._data[parameters["vendor"]][parameters["service"]]:
            self._data[parameters["vendor"]][parameters["service"]][parameters["region"]] = {parameters["type"]: {"value": price, "timestamp": timestamp}}
        else:
            self._data[parameters["vendor"]][parameters["service"]][parameters["region"]][parameters["type"]] = {"value": price, "timestamp": timestamp}


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
       }}""".format(**parameters)
        url = API_URL
        r = requests.post(url, json={"query": query}, headers={"X-Api-Key": self._key})
        if r.status_code != 200:
            print(f'POST Request failed with status code {r.status_code}')
            raise PriceNotFoundException
        result_json = r.json()
        print(result_json)
        try:
            price = float(result_json["data"]["products"][0]["prices"][0]["USD"])
        except:
            raise PriceNotFoundException
        self._set_price(parameters, price)
        self._save_data()
        return price

    def _read_api_key(self) -> str:
        try:
            with open(os.path.join(os.path.expanduser("~"), API_KEY_DIR), 'r') as file:
                for line in file.readlines():
                    match = re.search(r'api_key: (.*)', line)
                    if match:
                        return match.group(1)
                print("Could not find the API key in the '~/.config/infracost/credentials.yml' file")
        except FileNotFoundError:
            print("Could not find Infracost Cloud Pricing API key. Run 'infracost register' to generate a key")
        return ""
