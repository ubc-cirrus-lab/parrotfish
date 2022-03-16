from cmath import cos
import json
import time as time
import os
from spot.mlModel.polynomial_regression import PolynomialRegressionModel
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
from spot.definitions import ROOT_DIR
from spot.visualize.Plot import Plot
from spot.recommendation_engine.recommendation_engine import RecommendationEngine
from spot.constants import *


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

        try:
            self.last_log_timestamp = self.db.execute_max_value(
                self.config.function_name, DB_NAME_LOGS, "timestamp"
            )
        except:
            self.last_log_timestamp = (datetime.now() - datetime(1970, 1, 1)).total_seconds()

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
        self.recommendation_engine = RecommendationEngine(self.config_file_path, self.config, self.ml_model, self.db, self.benchmark_dir)

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

    # Runs the workload with different configs to profile the serverless function
    def profile(self):
        SMALLEST_MEM_SIZE = 256
        LARGEST_MEM_SIZE = 10240
        mem_size = SMALLEST_MEM_SIZE
        while mem_size <= LARGEST_MEM_SIZE:
            print("Invoking sample workload with mem_size: ", mem_size)
            # fetch configs and most up to date prices
            self.config_retriever.get_latest_config()
            self.price_retriever.fetch_current_pricing()
            self.function_invocator.invoke_all(mem_size)
            mem_size *= 2

    def update_config(self):
        self.recommendation_engine.update_config()

    def recommend(self):
        self.recommendation = self.recommendation_engine.recommend()

    def get_prediction_error_rate(self):
        # TODO: ensure it's called after update_config
        self.invoke()
        time.sleep(60)   # TODO:Turn this into async if you can
        # self.log_retriever.get_logs()
        self.collect_data()

        log_cnt = len(self.function_invocator.payload)
        self.ml_model.fetch_data(log_cnt)
        
        costs = self.ml_model._df["Cost"].values
        print(costs)
        # costs = np.array(costs)
        print(f"average: {np.mean(costs)}")
        print(f"median: {np.median(costs)}")
        err = abs(self.recommendation_engine.get_pred_cost() - np.median(costs)) / np.median(costs) * 100
        print(err)
        self.db.add_document_to_collection(self.config.function_name, DB_NAME_ERROR, {ERR_VAL: err})
        self.recommendation_engine.plot_config_vs_epoch()
        self.recommendation_engine.plot_error_vs_epoch()
        # return self.recommendation_engine.recommend() - np.median(costs)
