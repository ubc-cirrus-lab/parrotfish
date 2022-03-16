import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
import pickle
import sys
from spot.constants import COST, MEM_SIZE, REGION, RUNTIME, TIMEOUT, ARCH

from spot.db.db import DBClient
from sklearn.linear_model import SGDRegressor
from sklearn.model_selection import train_test_split

from spot.mlModel.ml_model_base_class import MlModelBaseClass


class LinearRegressionModel(MlModelBaseClass):
    def __init__(
        self, function_name, vendor, db: DBClient, last_log_timestamp, benchmark_dir
    ):
        super().__init__(function_name, vendor, db, last_log_timestamp)
        self._benchmark_dir = benchmark_dir
        self._ml_model_file_path = os.path.join(
            self._benchmark_dir, "linear_regression_model.pkl"
        )
        # try:
        #     self._model = pickle.load(open(self._ml_model_file_path, "rb"))
        # except:
        #     self._model = SGDRegressor(warm_start=True)

        self._model = SGDRegressor(warm_start=True)

    def _preprocess(self):
        # Transform numerical columns to categorical
        self._df.Runtime = pd.Categorical(self._df.Runtime)
        self._df["Runtime"] = self._df.Runtime.cat.codes

        self._df.Architectures = pd.Categorical(self._df.Architectures)
        self._df["Architectures"] = self._df.Architectures.cat.codes

        self._df.Region = pd.Categorical(self._df.Region)
        self._df["Region"] = self._df.Region.cat.codes

        # Create X matrix and Y vector for ML training
        # self._x = self._df[["Runtime", "Timeout", "MemorySize", "Architectures", "Region"]]
        self._x = self._df[[RUNTIME, TIMEOUT, MEM_SIZE, ARCH, REGION]]
        # self._x = self._df["MemorySize"]
        self._y = self._df[COST]

    def train_model(self):
        self._preprocess()
        X = self._x.values
        y = self._y.values

        X_mem = self._x[MEM_SIZE].values
        X_labels = np.unique(X_mem)
        mmap = {}
        for x in X_labels:
            idx = np.where(X_mem == x)
            mmap[x] = np.median(y[idx])
        X = X_labels.reshape(-1, 1)
        y = np.array(list(mmap.values()))
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=0
        )
        self._model.fit(X_train, y_train)
        test_err = self._model.score(X_test, y_test)
        print(f"model trained with testing error {test_err}")
        self._save_updated_model()

        plt.clf()
        plt.scatter(X, y, color="red")
        # plt.plot(X, self._model.predict(X), color='blue')

    def _save_updated_model(self):
        try:
            pickle.dump(self._model, open(self._ml_model_file_path, "wb"))
        except:
            f = open(self._ml_model_file_path, "w")
            f.close()
            pickle.dump(self._model, open(self._ml_model_file_path, "wb"))

    def get_memory_predictions(self):
        arr = {}
        mem_size = 128
        data = self._df[[RUNTIME, TIMEOUT, MEM_SIZE, ARCH, REGION]]

        data = data.iloc[0]

        while mem_size < 10240:
            data[MEM_SIZE] = mem_size
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
        return self._model.predict(new_x)

    """
    Creates and saves scatter plot of Memory Size vs Cost for the current serverless function
    """

    def _plot_memory_size_vs_cost(self):
        # Graph Setup
        plt.title("MemorySize vs Cost Graph for " + self._function_name)
        plt.xlabel("Memory(mB)", fontsize=7)
        plt.ylabel("Cost($)", fontsize=7)
        axes = plt.gca()
        plt.setp(axes.get_xticklabels(), rotation=90, fontsize=6)
        plt.setp(axes.get_yticklabels(), fontsize=6)

        # Format data in ascending memory size order
        zipped_list = zip(self._df[MEM_SIZE].values, self._df[COST].values)
        sorted_zipped_lists = sorted(zipped_list, key=lambda x: int(x[0]))
        x = [_ for _, element in sorted_zipped_lists]
        y = [element for _, element in sorted_zipped_lists]

        # Plot datapoints
        plt.scatter(x, y)

        # Add linear regression line
        x_vals = np.array(axes.get_xlim())
        y_vals = self._model.intercept_ + self._model.coef_[2] * x_vals
        plt.plot(
            x_vals,
            y_vals,
            "r-",
            label="y = "
            + str("{:.2E}".format(self._model.coef_[2]))
            + "x"
            + " + "
            + str("{:.2E}".format(self._model.intercept_)),
        )
        plt.legend()
        plt.show()

        # Save the plot with current timestamp
        today = datetime.datetime.now()
        timestamp = today.strftime("%Y-%m-%dT%H:%M:%S.%f+0000")
        plt.savefig(
            "spot/benchmarks/"
            + self._benchmark_dir
            + "/"
            + self._function_name
            + "-"
            + timestamp
            + ".png"
        )
