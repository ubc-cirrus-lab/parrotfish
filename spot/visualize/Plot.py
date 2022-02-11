import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import config_context
from sklearn.tree import plot_tree
from spot.db.db import DBClient

class Plot:
        def __init__(self, function_name, DBClient):
                self.function_name = function_name
                self.DBClient = DBClient


        def __fetch_config_vs_epoch_data(self):
                # gets all past configs associated with the current function name
                query_result = self.DBClient.execute_query(self.function_name, "suggested_configs", {}, {"mem_size":1, "_id":0})
                config_suggestions = []
                for config in query_result:
                        config_suggestions.append(config["mem_size"])

                return config_suggestions

        def __fetch_error_vs_epoch_data(self):
                #query_result = self.DBClient.execute_query(self.function_name, "memory_predictions", {}, {"MemorySize":1, "_id":0})
                pass

        def plot_config_vs_epoch(self):
                plt.title("MemorySize Suggestions vs Time for " + self.function_name)
                plt.ylabel("MemorySize(mB)", fontsize = 7)
                plt.xlabel("Epoch", fontsize = 7)
                axes = plt.gca()
                plt.setp(axes.get_xticklabels(), rotation=90, fontsize = 6)
                plt.setp(axes.get_yticklabels(), fontsize = 6)      


                config_suggestions = self.__fetch_config_vs_epoch_data()
                epochs = list(range(1, len(config_suggestions)+1))
                
                print(config_suggestions)
                # Plot datapoints
                plt.scatter(epochs, config_suggestions)

                # Save the plot with current timestamp
                today = datetime.datetime.now()
                timestamp = today.strftime( '%Y-%m-%dT%H:%M:%S.%f+0000')
                plt.savefig("spot/benchmarks/"+self.function_name+"/"+self.function_name + "-" + "config_vs_epoch_plot" + "-" +  timestamp + ".png")

        """ def plot_error_vs_epoch(self):   
                plt.title("Error vs Time for " + self.function_name)
                plt.xlabel("Error", fontsize = 7)
                plt.ylabel("Epoch", fontsize = 7)
                axes = plt.gca()
                plt.setp(axes.get_xticklabels(), rotation=90, fontsize = 6)
                plt.setp(axes.get_yticklabels(), fontsize = 6)      

                config_suggestions = self.__fetch_error_vs_epoch_data()
                epochs = list(1, len(config_suggestions))
                # Plot datapoints
                plt.scatter(epochs, config_suggestions)

                # Save the plot with current timestamp
                today = datetime.datetime.now()
                timestamp = today.strftime( '%Y-%m-%dT%H:%M:%S.%f+0000')
                plt.savefig("spot/benchmarks/"+self.function_name+"/"+self.function_name + "-" + "error_vs_epoch_plot" + "-" +  timestamp + ".png") """