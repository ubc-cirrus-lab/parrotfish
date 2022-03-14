import datetime
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn import config_context
from sklearn.tree import plot_tree
from spot.db.db import DBClient
from spot.constants import *


class Plot:
    def __init__(self, function_name: str, dbClient: DBClient, benchmark_dir: str):
        self.function_name = function_name
        self.dbClient = dbClient
        self.benchmark_dir = benchmark_dir

    def _fetch_config_vs_epoch_data(self):
        # gets all past configs associated with the current function name
        query_result = self.dbClient.execute_query(
            self.function_name, "suggested_configs", {}, {"mem_size": 1, "_id": 0}
        )
        config_suggestions = []
        for config in query_result:
            config_suggestions.append(config["mem_size"])

        return config_suggestions

    def _fetch_error_vs_epoch_data(self):
        query_result = self.dbClient.execute_query(self.function_name, DB_NAME_ERROR, {}, {ERR_VAL:1, "_id":0})
        return [res[ERR_VAL] for res in query_result]

    def plot_config_vs_epoch(self):
        plt.title("MemorySize Suggestions vs Time for " + self.function_name)
        plt.ylabel("MemorySize(mB)", fontsize=7)
        plt.xlabel("Epoch", fontsize=7)
        axes = plt.gca()
        plt.setp(axes.get_xticklabels(), rotation=90, fontsize=6)
        plt.setp(axes.get_yticklabels(), fontsize=6)

        config_suggestions = self._fetch_config_vs_epoch_data()
        epochs = list(range(1, len(config_suggestions) + 1))

        # Plot datapoints
        plt.scatter(epochs, config_suggestions)
        plt.plot(epochs, config_suggestions)

        # Save the plot with current timestamp
        today = datetime.datetime.now()
        timestamp = today.strftime("%Y-%m-%dT%H:%M:%S.%f+0000")

        save_dir = os.path.join(self.benchmark_dir, "config_vs_epoch")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
        plt.savefig(
            os.path.join(
                save_dir,
                f"{self.function_name}-config_vs_epoch_plot-{timestamp}.png",
            )
        )
        plt.clf()

    def plot_error_vs_epoch(self):   
        plt.title("Error vs Epoch for " + self.function_name)
        plt.xlabel("Epoch", fontsize = 7)
        plt.ylabel("Error(%)", fontsize = 7)
        axes = plt.gca()

        plt.setp(axes.get_xticklabels(), rotation=90, fontsize = 6)
        plt.setp(axes.get_yticklabels(), fontsize = 6)      

        err = self._fetch_error_vs_epoch_data()
        epochs = range(1, len(err) + 1)
      
        # Plot datapoints
        plt.scatter(epochs, err)
        plt.xticks(range(1, len(err) + 1))

        # Save the plot with current timestamp
        today = datetime.datetime.now()
        timestamp = today.strftime( '%Y-%m-%dT%H:%M:%S.%f+0000')

        save_dir = os.path.join(self.benchmark_dir, "error_vs_epoch")

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
        plt.savefig(
            os.path.join(
                save_dir,
                f"{self.function_name}-error_vs_epoch_plot-{timestamp}.png",
            )
        )
        plt.clf()
        
    def plot_epoch(self, plot_type: str):
        plt.title(f"{plot_type} vs Time for " + self.function_name)
        plt.xlabel(f"{plot_type}", fontsize = 7)
        plt.ylabel("Epoch", fontsize = 7)
        axes = plt.gca()
        plt.setp(axes.get_xticklabels(), rotation=90, fontsize = 6)
        plt.setp(axes.get_yticklabels(), fontsize = 6)
