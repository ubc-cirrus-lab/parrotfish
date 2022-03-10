import pandas as pd
import copy
from spot.db.db import DBClient

class MlModelBaseClass:
    def __init__(self, function_name, vendor, db: DBClient, last_log_timestamp):
        self._DBClient = db
        self._last_log_timestamp = last_log_timestamp
        self._function_name = function_name # TODO: folder name update
        self._df = pd.DataFrame(
            columns=[
                "Runtime",
                "Timeout",
                "MemorySize",
                "Architectures",
                "Region",
                "Cost",
            ]
        )
        self._vendor = vendor
        self._x = None
        self._y = None
        self._configs = None
        self._pricings = None
        self._logs = None
        self._log_query_results = None

    """ 
    Helper function, used for finding the corresponding configuration and pricing 
    that was in effect when a log is produced on a serverless function trigger
    Runtime: O(log n)
    """
    def _find_associated_index(self, list, field, left, right, target):
        if left > right:
            return -1

        mid = int((right + left) / 2)
        if list[mid][field] <= target:
            if mid + 1 == len(list):
                return mid
            else:
                if list[mid + 1][field] > target:
                    return mid
                else:
                    return self._find_associated_index(
                        list, field, mid + 1, right, target
                    )
        else:
            return self._find_associated_index(list, field, left, mid - 1, target)

    def _fetch_configs(self):
        # gets all past configs associated with the current function name
        config_query_result = self._DBClient.execute_query(
            self._function_name,
            "config",
            {},
            {
                "Runtime": 1,
                "Timeout": 1,
                "MemorySize": 1,
                "Architectures": 1,
                "LastModifiedInMs": 1,
                "_id": 0,
            },
        )
        self._configs = []
        for config in config_query_result:
            self._configs.append(config)

    def _fetch_pricings(self):
         # get all prices for the current function's cloud vendor
        pricing_query_result = self._DBClient.execute_query(
            "pricing",
            self._vendor,
            {},
            {
                "request_price": 1,
                "duration_price": 1,
                "region": 1,
                "timestamp": 1,
                "_id": 0,
            },
        )
        self._pricings = []
        for pricing in pricing_query_result:
            self._pricings.append(pricing)

    def _fetch_logs(self):
        # get all logs for this function
        self._log_query_result = self._DBClient.execute_query(
            self._function_name,
            "logs",
            {"timestamp": {"$gt": self._last_log_timestamp}}, # To process only unprocessed logs(aka iterative training)
            {"Billed Duration": 1, "Memory Size": 1, "timestamp": 1, "_id": 0},
        )
    
    """
    Find the config and pricing to associate with for every log of this function
    TODO: Rewrite reformatting section
    """
    def _associate_logs_with_config_and_pricing(self):
        for log in self._log_query_result:
            config_document_index = self._find_associated_index(
                self._configs, "LastModifiedInMs", 0, len(self._configs) - 1, log["timestamp"]
            )
            pricing_document_index = self._find_associated_index(
                self._pricings, "timestamp", 0, len(self._pricings) - 1, log["timestamp"]
            )

            # reformat the dataframe
            if current_config != -1 and current_pricing != -1:
                current_config = copy.deepcopy(self._configs[config_document_index])
                current_pricing = copy.deepcopy(self._pricings[pricing_document_index])

                new_row = current_config
                del new_row["LastModifiedInMs"]
                new_row["MemorySize"] = int(log["Memory Size"])
                new_row["Region"] = current_pricing["region"]
                new_row["Cost"] = (
                    float(current_pricing["duration_price"])
                    * float(log["Billed Duration"])
                    * float(int(log["Memory Size"]) / 128)
                )

                # self._df = self._df.append(new_row, ignore_index=True)
                self._df = pd.concat(
                    [self._df, pd.DataFrame.from_records([new_row])], ignore_index=True
                )

    """
    Fetches config, pricing and log data for the current function
    Associates config, pricing and log files by using timestamping comparison
    Fills dataframe via reformatting the fetched data
    """
    def fetch_data(self):
        self._fetch_configs()
        self._fetch_pricings()
        self._fetch_logs()
        self._associate_logs_with_config_and_pricing()
