import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import datetime
import pickle
from matplotlib.ticker import ScalarFormatter
from spot.mlModel.ml_model_base_class import MlModelBaseClass
from spot.constants import *
from spot.db.db import DBClient


class PolynomialRegressionModel(MlModelBaseClass):
    def __init__(
        self,
        function_name: str,
        vendor: str,
        db: DBClient,
        last_log_timestamp: int,
        benchmark_dir: str,
        mem_bounds: list,
        polynomial_degree=3,
    ):
        super().__init__(function_name, vendor, db, last_log_timestamp)
        self._degree = polynomial_degree
        self._benchmark_dir = benchmark_dir
        self._ml_model_file_path = (
            self._benchmark_dir
            + "/poly_regression_model-"
            + "degree_"
            + str(self._degree)
            + ".pkl"
        )

        self._x = None
        self._y = None
        try:
            self._model = pickle.load(open(self._ml_model_file_path, "rb"))
        except:
            self._model = None
        self.mem_bounds = mem_bounds

    def _preprocess(self):
        self._df[MEM_SIZE] = self._df[MEM_SIZE].astype(int)
        self._df = self._df[(self._df[MEM_SIZE] >= self.mem_bounds[0]) & (self._df[MEM_SIZE] <= self.mem_bounds[1])]
        X_mem = self._df[MEM_SIZE].values
        y = self._df[COST].values
        X_labels = np.unique(X_mem)
        mmap = {}
        for x in X_labels:
            idx = np.where(X_mem == x)
            mmap[x] = np.median(y[idx])

        self._x = X_labels
        self._y = np.array(list(mmap.values()))

    def _save_model(self):
        try:
            pickle.dump(self._model, open(self._ml_model_file_path, "wb"))
        except:
            f = open(self._ml_model_file_path, "w")
            f.close()
            pickle.dump(self._model, open(self._ml_model_file_path, "wb"))

    def train_model(self):
        self._preprocess()
        if self._x.size == 0 or self._y.size == 0:
            print("No data available to train the model")
            exit()

        self._model = np.polyfit(self._x, self._y, self._degree)
        self._save_model()

    """
    Creates and saves scatter plot of Memory Size vs Cost for the current serverless function
    """

    def plot_memsize_vs_cost(self):
        # Graph Setup
        plt.title("MemorySize vs Cost Graph for " + self._function_name)
        plt.xlabel("Memory(mB)", fontsize=7)
        plt.ylabel("Cost($)", fontsize=7)
        axes = plt.gca()

        # axes.set_xscale("log")
        plt.setp(axes.get_xticklabels(), rotation=90, fontsize=6)
        plt.setp(axes.get_yticklabels(), fontsize=6)

        # axes.xaxis.set_major_formatter(ScalarFormatter())

        # Plot datapoints
        plt.scatter(self._x, self._y)

        # Add linear regression line
        xvars = np.linspace(self._x.min(), self._x.max(), 1024)
        plt.plot(
            xvars,
            np.polyval(self._model, xvars),
            label=self.get_polynomial_equation_string(),
            color="red",
        )

        # Get optimal config
        x_min, y_min = self.get_optimal_config()

        print(f"Minimum cost of {y_min} found at {x_min} MB")

        # Plot best mem size, data points and polynomial regression fit
        plt.plot(x_min, y_min, "x")
        plt.legend()
        plt.show()

        # Save the plot with current timestamp
        today = datetime.datetime.now()
        timestamp = today.strftime("%Y-%m-%dT%H:%M:%S.%f+0000")
        save_dir = os.path.join(self._benchmark_dir, "memsize_vs_cost")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(
            os.path.join(
                save_dir,
                f"{self._function_name}-memsize_vs_cost_graph_polynomial-{timestamp}.png",
            )
        )
        plt.clf()

    def get_polynomial_equation_string(self):
        ret_val = ""
        for degree in range(len(self._model) - 1, -1, -1):
            if degree == 0:
                ret_val += str(round(self._model[degree],3))
            else:
                ret_val += (
                    str("{:.2E}".format(self._model[degree]))
                    + "x^"
                    + str(degree)
                    + " + "
                )
        return ret_val

    def predict(self, X):
        return self._model.predict(X)

    # Compute global minima including range boundaries
    def get_optimal_config(self):
        if self._model is None:
            print("ML model not trained yet, thus can't recommend optimal config")
            exit()
        c = np.poly1d(self._model)
        bounds = self.mem_bounds

        x_min = None
        y_min = None
        crit_points = bounds + [
            x for x in c.deriv().r if x.imag == 0 and bounds[0] < x.real < bounds[1]
        ]
        for x in crit_points:
            if y_min is None:
                y_min = c(x)
                x_min = x
            elif y_min > c(x):
                x_min = x
                y_min = c(x)

        # Check if model suggest mathematically possible config
        if x_min is None:
            print("Model can't suggest mathematically possible solution")
            exit()
        else:
            y_min = c(x_min)
            return x_min, y_min
