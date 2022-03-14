from cmath import cos
import json
import time as time
import os
from spot.mlModel.polynomial_regression import PolynomialRegressionModel
import numpy as np

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
from spot.recommendation_engine.recommendation_engine import RecommendationEngine


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
        self.last_log_timestamp = 0

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
        self.recommendation_engine = RecommendationEngine(
            self.config_file_path, self.config, self.ml_model, self.db
        )

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
        self.ml_model.fetch_data()
        self.ml_model.train_model()

    def select_model(self, model):
        if model == "LinearRegression":
            return LinearRegressionModel(
                self.config.function_name,
                self.config.vendor,
                self.db,
                self.last_log_timestamp,
                self.benchmark_dir,
            )
        if model == "polynomial":
            return PolynomialRegressionModel(
                self.config.function_name,
                self.config.vendor,
                self.db,
                self.last_log_timestamp,
                self.benchmark_dir,
            )

    def profile(self):
        self.function_invocator.profile()

    def update_config(self):
        self.recommendation_engine.update_config()

    def recommend(self):
        self.recommendation = self.recommendation_engine.recommend()

    def get_prediction_error_rate(self):
        # TODO: ensure it's called after update_config
        self.invoke()
        time.sleep(60)
        # self.log_retriever.get_logs()
        self.collect_data()

        log_cnt = len(self.function_invocator.payload)
        top_logs_from_db = self.db.get_top_docs(
            self.config.function_name, "logs", log_cnt
        )
        logs = [log for log in top_logs_from_db]
        costs = []
        self.ml_model.fetch_data()
        for log in logs:
            cost = (
                float(self.ml_model._pricings[0]["duration_price"])
                * float(log["Billed Duration"])
                * float(int(log["Memory Size"]) / 128)
            )
            costs.append(cost)
        costs = np.array(costs)
        print(f"average: {np.mean(costs)}")
        print(f"median: {np.median(costs)}")
        self.recommendation_engine.plot_config_vs_epoch()
        return self.recommendation_engine.recommend() - np.median(costs)
