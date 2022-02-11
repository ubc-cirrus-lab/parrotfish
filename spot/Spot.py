from spot.prices.aws_price_retriever import AWSPriceRetriever
from spot.logs.aws_log_retriever import AWSLogRetriever
from spot.invocation.aws_function_invocator import AWSFunctionInvocator
from spot.configs.aws_config_retriever import AWSConfigRetriever
from spot.mlModel.linear_regression import LinearRegressionModel
from spot.invocation.config_updater import ConfigUpdater
from spot.db.db import DBClient
from spot.visualize.Plot import Plot
import json
import time as time
import os


class Spot:
    def __init__(self, config_file_path="spot/config.json"):
        # Load configuration values from config.json
        self.config = None
        self.config_file_path = config_file_path

        with open(config_file_path) as f:
            self.config = json.load(f)
            with open(self.config["workload_path"], "w") as json_file:
                json.dump(self.config["workload"], json_file)

        try:
            benchmark_dir = self.config["folder_name"]
        except KeyError:
            benchmark_dir = None

        # Instantiate SPOT system components
        self.price_retriever = AWSPriceRetriever(
            self.config["DB_URL"], self.config["DB_PORT"], self.config["region"]
        )
        self.log_retriever = AWSLogRetriever(
            self.config["function_name"],
            self.config["DB_URL"],
            self.config["DB_PORT"],
            self.config["last_log_timestamp"],
        )
        self.function_invocator = AWSFunctionInvocator(
            self.config["workload_path"],
            self.config["function_name"],
            self.config["mem_size"],
            self.config["region"],
        )
        self.config_retriever = AWSConfigRetriever(
            self.config["function_name"], self.config["DB_URL"], self.config["DB_PORT"]
        )
        self.ml_model = LinearRegressionModel(
            self.config["function_name"],
            self.config["vendor"],
            self.config["DB_URL"],
            self.config["DB_PORT"],
            self.config["last_log_timestamp"],
            benchmark_dir,
        )  # TODO: Parametrize ML model constructor with factory method
        self.DBClient = DBClient(self.config["DB_URL"], self.config["DB_PORT"])

    def __del__(self):

        # Save the updated configurations
        with open(self.config_file_path, "w") as f:
            json.dump(self.config, f)

        # Update the memory config on AWS with the newly suggested memory size
        config_updater = ConfigUpdater(
            self.config["function_name"], self.config["mem_size"], self.config["region"]
        )
        config_updater.set_mem_size(self.config["mem_size"])

        # Save model config suggestions
        self.DBClient.add_document_to_collection(self.config["function_name"], "suggested_configs", self.config)

        # Save model predictions to db for error calculation
        # self.DBClient.add_document_to_collection(self.config["function_name"], "memory_predictions", memory_predictions)

        plotter = Plot(self.config["function_name"], self.DBClient)
        plotter.plot_config_vs_epoch()

    def execute(self):
        print("Invoking function:", self.config["function_name"])
        # invoke the indicated function
        self.invoke_function()

        print("Sleeping to allow logs to propogate")
        #wait to allow logs to populate in aws
        time.sleep(15) # TODO: Change this to waiting all threads to yield

        print("Retrieving new logs and save in db")
        # collect log data
        self.collect_data()

        print("Training ML model")
        # train ML model accordingly
        self.train_model()

    def invoke_function(self):
        # fetch configs and most up to date prices
        self.config_retriever.get_latest_config()
        self.price_retriever.fetch_current_pricing()

        # invoke function
        self.function_invocator.invoke_all()

    def collect_data(self):
        # retrieve logs
        self.config["last_log_timestamp"] = self.log_retriever.get_logs()

    def train_model(self):
        # only train the model, if new logs are introduced
        if self.ml_model.fetch_data():
            new_configs, memory_predictions = self.ml_model.train_model()

            # update config fields with new configs(currently only mem_size)
            for new_config in new_configs:
                self.config[new_config] = new_configs[new_config]
