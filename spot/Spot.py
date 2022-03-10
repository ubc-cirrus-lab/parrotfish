import json
import time as time
import os

from spot.prices.aws_price_retriever import AWSPriceRetriever
from spot.logs.aws_log_retriever import AWSLogRetriever
from spot.invocation.aws_function_invocator import AWSFunctionInvocator
from spot.configs.aws_config_retriever import AWSConfigRetriever
from spot.mlModel.linear_regression import LinearRegressionModel
from spot.invocation.config_updater import ConfigUpdater
from spot.db.db import DBClient
from spot.benchmark_config import BenchmarkConfig
from spot.definitions import ROOT_DIR
from spot.visualize.Plot import Plot


class Spot:
    def __init__(self, config_dir: str, model: str):
        # Load configuration values from config.json
        self.config: BenchmarkConfig
        self.path: str = config_dir
        self.workload_file_path = os.path.join(self.path, "workload.json")
        self.config_file_path = os.path.join(self.path, "config.json")
        self.db = DBClient()

        with open(self.config_file_path) as f:
            self.config = BenchmarkConfig()
            self.config.deserialize(f)
            with open(self.workload_file_path, "w") as json_file:
                json.dump(self.config.workload, json_file, indent=4)

        self.benchmark_dir = self.path

        self.last_log_timestamp = self.db.execute_max_value(
            self.config.function_name, "logs", "timestamp"
        )

        # Instantiate SPOT system components
        self.price_retriever = AWSPriceRetriever(self.db, self.config.region)
        self.log_retriever = AWSLogRetriever(
            self.config.function_name,
            self.db,
            self.last_log_timestamp,
        )
        self.function_invocator = AWSFunctionInvocator(
            self.workload_file_path,
            self.config.function_name,
            self.config.mem_size,
            self.config.region,
        )
        self.config_retriever = AWSConfigRetriever(self.config.function_name, self.db)
        self.ml_model = self.select_model(model)
    # TODO: Move this to recommendation engine
    def update_config(self):

        # Save the updated configurations
        with open(self.config_file_path, "w") as f:
            f.write(self.config.serialize())

        # Update the memory config on AWS with the newly suggested memory size
        config_updater = ConfigUpdater(
            self.config.function_name, self.config.mem_size, self.config.region
        )

        # Save model config suggestions
        self.db.add_document_to_collection(
            self.config.function_name, "suggested_configs", self.config.get_dict()
        )

        # Save model predictions to db for error calculation
        # self.db.add_document_to_collection(self.config.function_name, "memory_predictions", memory_predictions)

        #plotter = Plot(self.config.function_name, self.db, directory=self.path)
        #plotter.plot_config_vs_epoch()

    def execute(self):
        print("Invoking function:", self.config.function_name)
        # invoke the indicated function
        self.invoke()

        print("Sleeping to allow logs to propogate")
        # wait to allow logs to populate in aws
        time.sleep(15)  # TODO: Change this to waiting all threads to yield

        print("Retrieving new logs and save in db")
        # collect log data
        self.collect_data()

        print("Training ML model")
        # train ML model accordingly
        self.train_model()

    def invoke(self):
        # fetch configs and most up to date prices
        self.config_retriever.get_latest_config()
        self.price_retriever.fetch_current_pricing()

        # invoke function
        self.function_invocator.invoke_all()

    def collect_data(self):
        # retrieve logs
        self.last_log_timestamp = self.log_retriever.get_logs()

    def train_model(self):
        # only train the model, if new logs are introduced
        if self.ml_model.fetch_data():
            new_configs, memory_predictions = self.ml_model.train_model()

            # update config fields with new configs(currently only mem_size) TODO: Update memory config and other parameters
            for new_config in new_configs:
                self.config[new_config] = new_configs[new_config]

    def select_model(self, model):
        if(model == "LinearRegression"):
            return LinearRegressionModel(
            self.config.function_name,
            self.config.vendor,
            self.db,
            self.last_log_timestamp,
            self.benchmark_dir,
        )
