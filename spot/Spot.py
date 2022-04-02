import sys
import json
import time
import os
import numpy as np
from datetime import datetime
from spot.prices.aws_price_retriever import AWSPriceRetriever
from spot.logs.aws_log_retriever import AWSLogRetriever
from spot.invocation.aws_function_invocator import AWSFunctionInvocator
from spot.configs.aws_config_retriever import AWSConfigRetriever
from spot.mlModel.linear_regression import LinearRegressionModel
from spot.invocation.config_updater import ConfigUpdater
from spot.db.db import DBClient
from spot.benchmark_config import BenchmarkConfig
from spot.constants import ROOT_DIR
from spot.visualize.Plot import Plot
from spot.recommendation_engine.recommendation_engine import RecommendationEngine
from spot.constants import *
from spot.mlModel.polynomial_regression import PolynomialRegressionModel
from spot.logs.log_propagation_waiter import LogPropagationWaiter


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
        self.log_prop_waiter = LogPropagationWaiter(self.config.function_name)

        try:
            self.last_log_timestamp = self.db.execute_max_value(
                self.config.function_name, DB_NAME_LOGS, "timestamp"
            )
        except:
            print(
                "No data for the serverless function found yet. Setting last timestamp for the serverless function to 0.",
            )
            self.last_log_timestamp = 0

        # Create function db if not exists
        self.db.create_function_db(self.config.function_name)

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
            self.config_file_path,
            self.config,
            self.ml_model,
            self.db,
            self.benchmark_dir,
        )

    def invoke(self):
        # fetch configs and most up to date prices
        self.config_retriever.get_latest_config()
        self.price_retriever.fetch_current_pricing()

        # invoke function
        start = datetime.now().timestamp()
        self.function_invocator.invoke_all()
        self.log_prop_waiter.wait_by_count(start, self.function_invocator.invoke_cnt)

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
                self.config.mem_bounds,
            )

    # Runs the workload with different configs to profile the serverless function
    def profile(self):
        mem_size = self.config.mem_bounds[0]
        start = datetime.now().timestamp()
        invoke_cnt = 0
        while mem_size <= self.config.mem_bounds[1]:
            print("Invoking sample workload with mem_size: ", mem_size)
            # fetch configs and most up to date prices
            self.config_retriever.get_latest_config()
            self.price_retriever.fetch_current_pricing()
            self.function_invocator.invoke_all(mem_size)
            invoke_cnt += self.function_invocator.invoke_cnt
            mem_size *= 2
        self.log_prop_waiter.wait_by_count(start, invoke_cnt)

    def update_config(self):
        self.recommendation_engine.update_config()

    def plot_error_vs_epoch(self):
        self.recommendation_engine.plot_error_vs_epoch()

    def plot_config_vs_epoch(self):
        self.recommendation_engine.plot_config_vs_epoch()

    def plot_memsize_vs_cost(self):
        self.ml_model.plot_memsize_vs_cost()

    def recommend(self):
        self.recommendation = self.recommendation_engine.recommend()

    def get_prediction_error_rate(self):
        # TODO: ensure it's called after update_config
        self.invoke()
        self.collect_data()

        log_cnt = len(self.function_invocator.payload)
        self.ml_model.fetch_data(log_cnt)

        costs = self.ml_model._df["Cost"].values
        pred = self.recommendation_engine.get_pred_cost()
        err = sum([(cost - pred) ** 2 for cost in costs]) / len(costs)
        print(f"{err=}")
        self.db.add_document_to_collection(
            self.config.function_name, DB_NAME_ERROR, {ERR_VAL: err}
        )
        self.recommendation_engine.plot_config_vs_epoch()
        self.recommendation_engine.plot_error_vs_epoch()
