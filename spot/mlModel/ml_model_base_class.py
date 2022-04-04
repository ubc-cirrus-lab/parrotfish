import pandas as pd
import copy

from spot.db.db import DBClient
from spot.constants import *


class MlModelBaseClass:
    def __init__(self, function_name, vendor, db: DBClient, last_log_timestamp):
        self._DBClient = db
        self._last_log_timestamp = last_log_timestamp
        self._function_name = function_name  # TODO: folder name update
        self._df = pd.DataFrame(
            # columns=[
            #     "Runtime",
            #     "Timeout",
            #     MEM_SIZE,
            #     "Architectures",
            #     REGION,
            #     COST,
            # ]
            columns=[RUNTIME, TIMEOUT, MEM_SIZE, ARCH, REGION, COST]
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
            DB_NAME_CONFIG,
            {},
            {
                RUNTIME: 1,
                TIMEOUT: 1,
                ARCH: 1,
                LAST_MODIFIED_MS: 1,
                DB_ID: 0,
            },
        )
        self._configs = [config for config in config_query_result]

    def _fetch_pricings(self):
        # get all prices for the current function's cloud vendor
        pricing_query_result = self._DBClient.execute_query(
            DB_NAME_PRICING,
            self._vendor,
            {},
            {
                REQUEST_PRICE: 1,
                DURATION_PRICE: 1,
                REGION: 1,
                TIMESTAMP: 1,
                DB_ID: 0,
            },
        )
        self._pricings = []
        for pricing in pricing_query_result:
            self._pricings.append(pricing)

    def _fetch_logs(self):
        # get all logs for this function
        self._log_query_result = self._DBClient.execute_query(
            self._function_name,
            DB_NAME_LOGS,
            {
                "timestamp": {"$gt": 0}
            },  # To process only unprocessed logs(aka iterative training)
            {BILLED_DURATION: 1, MEM_SIZE: 1, TIMESTAMP: 1, DB_ID: 0},
        )

    """
    Find the config and pricing to associate with for every log of this function
    TODO: Rewrite reformatting section
    """

    def _associate_logs_with_config_and_pricing(self):
        for log in self._log_query_result:
            config_document_index = self._find_associated_index(
                self._configs,
                LAST_MODIFIED_MS,
                0,
                len(self._configs) - 1,
                log[TIMESTAMP],
            )
            pricing_document_index = self._find_associated_index(
                self._pricings,
                TIMESTAMP,
                0,
                len(self._pricings) - 1,
                log[TIMESTAMP],
            )

            # reformat the dataframe
            if config_document_index != -1 and pricing_document_index != -1:
                current_config = copy.deepcopy(self._configs[config_document_index])
                current_pricing = copy.deepcopy(self._pricings[pricing_document_index])
                self.current_pricing = current_pricing
                new_row = current_config
                del new_row[LAST_MODIFIED_MS]
                new_row[MEM_SIZE] = int(log[MEM_SIZE])
                new_row[REGION] = current_pricing[REGION]
                new_row[COST] = (
                    float(current_pricing[DURATION_PRICE])
                    * float(log[BILLED_DURATION])
                    * float(int(log[MEM_SIZE]) / 128)
                )

                self._df = pd.concat(
                    [self._df, pd.DataFrame.from_records([new_row])], ignore_index=True
                )

    """
    Fetches config, pricing and log data for the current function
    Associates config, pricing and log files by using timestamping comparison
    Fills dataframe via reformatting the fetched data
    """

    def fetch_data(self, log_cnt=None) -> None:
        self._fetch_configs()
        self._fetch_pricings()
        self._get_top_logs(log_cnt) if log_cnt else self._fetch_logs()
        self._associate_logs_with_config_and_pricing()
        # return self._log_query_result != 0

    def get_optimal_config(self):
        pass

    def plot_memsize_vs_cost(self):
        pass

    def _get_top_logs(self, log_cnt: int) -> None:
        self._log_query_result = self._DBClient.get_top_docs(
            self._function_name, DB_NAME_LOGS, log_cnt
        )
