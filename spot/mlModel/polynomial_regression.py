import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
import pickle
from matplotlib.ticker import ScalarFormatter
from spot.mlModel.ml_model_base_class import MlModelBaseClass
from spot.constants import *
from spot.db.db import DBClient


class PolynomialRegressionModel(MlModelBaseClass):
    def __init__(
        self, function_name, vendor, db: DBClient, last_log_timestamp, benchmark_dir
    ):
        super().__init__(function_name, vendor, db, last_log_timestamp)
        self._benchmark_dir = benchmark_dir
        self._ml_model_file_path = os.path.join(
            self._benchmark_dir, "poly_regression_model.pkl"
        )
        self._x = None
        self._y = None
        try:
            self._model = pickle.load(open(self._ml_model_file_path, "rb"))
        except:
            self._model = None

    def _preprocess(self):
        self._df[MEM_SIZE] = self._df[MEM_SIZE].astype(int)
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

        self._model = np.polyfit(self._x, self._y, 4)
        self._save_model()
        self.plot_memsize_vs_cost()

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
        xvars = np.linspace(np.min(self._x), np.max(self._x), 1024)
        plt.plot(
            xvars,
            np.polyval(self._model, xvars),
            label=self.get_polynomial_equation_string(),
            color="red",
        )

        # Get optimal config
        x_min, y_min = self.get_optimal_config()

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
        for degree in range(len(self._model) - 1, 0, -1):
            if degree == 0:
                ret_val += str(self._model[degree])
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
        bounds = [256, 10280]

        crit = c.deriv().r
        r_crit = crit[crit.imag == 0].real
        test = c.deriv(2)(r_crit)

        x_min = max(r_crit[test > 0][0], bounds[0])
        y_min = c(x_min)
        
        # Check if model suggest mathematically possible config
        if x_min < bounds[0] or x_min > bounds[1] or y_min < 0:
            print("Model can't suggest mathematically possible solution")
            exit()

        left_boundary_cost = c(bounds[0])
        right_boundary_cost = c(bounds[1])
        if left_boundary_cost >= 0 and left_boundary_cost < y_min:
            y_min = left_boundary_cost
            x_min = bounds[0]
        if right_boundary_cost >= 0 and right_boundary_cost < y_min:
            y_min = right_boundary_cost
            x_min = bounds[1]

        x_min = int(x_min)
        return x_min, y_min
