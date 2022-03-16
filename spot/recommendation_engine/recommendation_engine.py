import boto3 
import datetime
import os

from spot.invocation.config_updater import ConfigUpdater
from spot.visualize.Plot import Plot
from spot.constants import *

class RecommendationEngine:
    def __init__(self, config_file_path, config, model, db, benchmark_dir):
        self.config_file_path = config_file_path
        self._model = model
        self.new_config = config
        self.db = db
        self.plotter = Plot(self.new_config.function_name, self.db, benchmark_dir)
        self.x_min = None
        self.y_min = None


    def recommend(self):
        """get optimal mem config from the model"""
        self.x_min, self.y_min = self._model.get_optimal_config()
        print("Best memory config: ", self.x_min, "  ", "Cost: ", self.y_min)
        return self.x_min
        
    def get_pred_cost(self):
        return self.y_min

    def update_config(self):

        # Get the new recommended config
        self.new_config.mem_size = self.recommend()

        # Save the updated configurations
        with open(self.config_file_path, "w") as f:
            f.write(self.new_config.serialize())

        # Update the memory config on AWS with the newly suggested memory size
        ConfigUpdater(
            self.new_config.function_name,
            self.new_config.mem_size,
            self.new_config.region,
        )
        timestamp = datetime.datetime.now()

        # Save model config suggestions
        self.db.add_document_to_collection(
            self.new_config.function_name,
            "suggested_configs",
            self.new_config.get_dict(),
        )

        # Save model predictions to db for error calculation
        #self.db.add_document_to_collection(self.new_config.function_name, "memory_predictions", {"mem_size": self.new_config.mem_size})
        #self.plot_config_vs_epoch()

        #invoke

        #fetch new data

        #run query, as in mlmodel base class fetch data, to get the new logs after the timestamp

        #get the median cost of these new logs

        #compare this cost with predicted

        #save it into db

        #plot

    def plot_config_vs_epoch(self):
        self.plotter.plot_config_vs_epoch()

    def plot_error_vs_epoch(self):
        self.plotter.plot_error_vs_epoch()

    