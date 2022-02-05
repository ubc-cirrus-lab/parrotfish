import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import config_context
from sklearn.tree import plot_tree

class Plot:
        def __init__(self, function_name):
                self.function_name = function_name

        def __fetch_config_vs_epoch_data(self):
                # gets all past configs associated with the current function name
                query_result = self.DBClient.execute_query(self.function_name, "suggested_configs", {}, {"MemorySize":1, "_id":0})
                config_suggestions = []
                for config in query_result:
                        config_suggestions.append(config)

                return config_suggestions

        def plot_config_vs_epoch(self):
                plt.title("MemorySize Suggestions vs Time for " + self.function_name)
                plt.xlabel("MemorySize(mB)", fontsize = 7)
                plt.ylabel("Epoch", fontsize = 7)
                axes = plt.gca()
                plt.setp(axes.get_xticklabels(), rotation=90, fontsize = 6)
                plt.setp(axes.get_yticklabels(), fontsize = 6)      


                config_suggestions = self.fetch_config_vs_epoch_data()
                epochs = list(1, len(config_suggestions))
                # Plot datapoints
                plt.scatter(epochs, config_suggestions)

plotter = Plot("AWSHelloWorld")
plotter.plot_config_vs_epoch()