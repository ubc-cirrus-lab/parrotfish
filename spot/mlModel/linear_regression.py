import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import pickle
import sys
import copy
from spot.db.db import DBClient
from sklearn.linear_model import SGDRegressor


class LinearRegressionModel:
    def __init__(
        self, function_name, vendor, url, port, last_log_timestamp, benchmark_dir
    ):
        self.url = url
        self.port = port
        self.DBClient = DBClient(self.url, self.port)
        self.last_log_timestamp = last_log_timestamp

        self.function_name = function_name

        self.ml_model_file_path = (
            "spot/benchmarks/"
            + (benchmark_dir or self.function_name)
            + "/linear_regression_model.pkl"
        )
        try:
            self.model = pickle.load(open(self.ml_model_file_path, "rb"))
        except:
            self.model = SGDRegressor(
                warm_start=True
            )  # TODO: Check the accuracy of warm_start

        self.df = pd.DataFrame(
            columns=[
                "Runtime",
                "Timeout",
                "MemorySize",
                "Architectures",
                "Region",
                "Cost",
            ]
        )
        self.vendor = vendor

    """ 
    Helper function, used for finding the corresponding configuration and pricing 
    that was in effect when a log is produced on a serverless function trigger
    """

    def find_associated_index(self, list, field, left, right, target):
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
                    return self.find_associated_index(
                        list, field, mid + 1, right, target
                    )
        else:
            return self.find_associated_index(list, field, left, mid - 1, target)

    """
    Fetches config, pricing and log data for the current function
    Associates config, pricing and log files by using timestamping comparison
    Fills dataframe via reformatting the fetched data
    """

    def fetch_data(self):
        # gets all past configs associated with the current function name
        config_query_result = self.DBClient.execute_query(
            self.function_name,
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
        configs = []
        for config in config_query_result:
            configs.append(config)

        # get all prices for the current function's cloud vendor
        pricing_query_result = self.DBClient.execute_query(
            "pricing",
            self.vendor,
            {},
            {
                "request_price": 1,
                "duration_price": 1,
                "region": 1,
                "timestamp": 1,
                "_id": 0,
            },
        )
        pricings = []
        for pricing in pricing_query_result:
            pricings.append(pricing)

        # get all logs for this function
        log_query_result = self.DBClient.execute_query(
            self.function_name,
            "logs",
            {"timestamp": {"$gt": 0}},
            {"Billed Duration": 1, "Memory Size": 1, "timestamp": 1, "_id": 0},
        )

        # find the config and pricing to associate with for every log of this function
        new_log_count = 0
        for log in log_query_result:
            new_log_count += 1
            current_config = self.find_associated_index(
                configs, "LastModifiedInMs", 0, len(configs) - 1, log["timestamp"]
            )
            current_pricing = self.find_associated_index(
                pricings, "timestamp", 0, len(pricings) - 1, log["timestamp"]
            )

            # reformat the dataframe
            if current_config != -1 and current_pricing != -1:
                current_config = copy.deepcopy(configs[current_config])
                current_pricing = copy.deepcopy(pricings[current_pricing])

                new_row = current_config
                del new_row["LastModifiedInMs"]
                new_row["MemorySize"] = log["Memory Size"]
                new_row["Region"] = current_pricing["region"]
                new_row["Cost"] = (
                    float(current_pricing["duration_price"])
                    * float(log["Billed Duration"])
                    * float(int(log["Memory Size"]) / 128)
                )

                self.df = self.df.append(new_row, ignore_index=True)

        # Return true, if any new logs are introduced
        return True if new_log_count > 0 else False

    def train_model(self):
        # Transform numerical columns to categorical
        self.df.Runtime = pd.Categorical(self.df.Runtime)
        self.df["Runtime"] = self.df.Runtime.cat.codes

        self.df.Architectures = pd.Categorical(self.df.Architectures)
        self.df["Architectures"] = self.df.Architectures.cat.codes

        self.df.Region = pd.Categorical(self.df.Region)
        self.df["Region"] = self.df.Region.cat.codes

        # Create X matrix and Y vector for ML training
        x = self.df[["Runtime", "Timeout", "MemorySize", "Architectures", "Region"]]
        y = self.df["Cost"]

        # Create and train the model
        self.model.fit(x.values, y.values)
        try:
            pickle.dump(self.model, open(self.ml_model_file_path, "wb"))
        except:
            f = open(self.ml_model_file_path, "w")
            f.close()
            pickle.dump(self.model, open(self.ml_model_file_path, "wb"))

        # Print results and create scatter plot
        print("intercept:", self.model.intercept_)
        print("slope:", self.model.coef_)
        new_configs = {}
        mem_predictions = self.get_memory_predictions()
        new_configs["mem_size"] = self.get_best_memory_config(mem_predictions)
        return [new_configs, mem_predictions]

    def get_memory_predictions(self):
        arr = {}
        mem_size = 128
        data = self.df[["Runtime", "Timeout", "MemorySize", "Architectures", "Region"]]
        data = data.iloc[0]

        while mem_size < 10240:
            data["MemorySize"] = mem_size
            new_x = data.to_numpy()
            new_x = new_x.reshape(1, -1)
            arr[mem_size] = self.predict(new_x)[0]
            mem_size *= 2
        return arr

    def get_best_memory_config(self, options):
        min_cost = sys.float_info.max
        best_mem_option = 128
        for mem, price in options.items():
            if min_cost < price:
                best_mem_option = mem
                min_cost = price

        return best_mem_option

    """
    Predicts the price outcome of given values in our ML model
    """

    def predict(self, new_x):
        return self.model.predict(new_x)

    """
    Creates and saves scatter plot of Memory Size vs Cost for the current serverless function
    """

    def show_graph(self):
        # Graph Setup
        plt.title("MemorySize vs Cost Graph for " + self.function_name)
        plt.xlabel("Memory(mB)", fontsize=7)
        plt.ylabel("Cost($)", fontsize=7)
        axes = plt.gca()
        plt.setp(axes.get_xticklabels(), rotation=90, fontsize=6)
        plt.setp(axes.get_yticklabels(), fontsize=6)

        # Format data in ascending memory size order
        zipped_list = zip(self.df["MemorySize"].values, self.df["Cost"].values)
        sorted_zipped_lists = sorted(zipped_list, key=lambda x: int(x[0]))
        x = [_ for _, element in sorted_zipped_lists]
        y = [element for _, element in sorted_zipped_lists]

        # Plot datapoints
        plt.scatter(x, y)

        # Add linear regression line
        x_vals = np.array(axes.get_xlim())
        y_vals = self.model.intercept_ + self.model.coef_[2] * x_vals
        plt.plot(
            x_vals,
            y_vals,
            "r-",
            label="y = "
            + str("{:.2E}".format(self.model.coef_[2]))
            + "x"
            + " + "
            + str("{:.2E}".format(self.model.intercept_)),
        )
        plt.legend()
        plt.show()

        # Save the plot with current timestamp
        today = datetime.datetime.now()
        timestamp = today.strftime("%Y-%m-%dT%H:%M:%S.%f+0000")
        plt.savefig(
            "spot/benchmarks/"
            + self.function_name
            + "/"
            + self.function_name
            + "-"
            + timestamp
            + ".png"
        )
