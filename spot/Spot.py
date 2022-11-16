import sys
import json
import time
import os
import numpy as np
import pickle
from datetime import datetime
from spot.prices.aws_price_retriever import AWSPriceRetriever
from spot.logs.aws_log_retriever import AWSLogRetriever
from spot.invocation.aws_lambda_invoker import AWSLambdaInvoker
from spot.context import Context
from spot.benchmark_config import BenchmarkConfig
from spot.recommendation_engine.recommendation_engine import RecommendationEngine
from spot.constants import *


class Spot:
    def __init__(self, config_dir: str, aws_session):
        # Load configuration values from config.json
        self.config: BenchmarkConfig
        self.path: str = config_dir
        self.workload_file_path = os.path.join(self.path, "workload.json")
        self.config_file_path = os.path.join(self.path, "config.json")

        # TODO: implement checkpoint & restore on Context (loading from pickle?).
        self.ctx = Context()

        with open(self.config_file_path) as f:
            self.config = BenchmarkConfig()
            self.config.deserialize(f)
            with open(self.workload_file_path, "w") as json_file:
                json.dump(self.config.workload, json_file, indent=4)

        self.benchmark_dir = self.path

        # try:
        #    self.last_log_timestamp = self.ctx.execute_max_value(
        #        self.config.function_name, DB_NAME_LOGS, "timestamp"
        #    )
        # except:
        #    print(
        #        "No data for the serverless function found yet. Setting last timestamp for the serverless function to 0.",
        #    )
        #    self.last_log_timestamp = None
        self.last_log_timestamp = None

        self.ctx.create_function_df(self.config.function_name)

        # Instantiate SPOT system components
        self.price_retriever = AWSPriceRetriever(self.ctx, self.config.region)
        self.log_retriever = AWSLogRetriever(
            self.ctx, aws_session, self.config.function_name
        )
        function_invoker = AWSLambdaInvoker(aws_session, self.config.function_name)
        self.recommendation_engine = RecommendationEngine(
            function_invoker, self.workload_file_path, self.config.workload
        )

    def optimize(self):
        self.recommendation_engine.run()

    def collect_data(self):
        # retrieve latest config, logs, pricing scheme
        self.price_retriever.fetch_current_pricing()
        self.last_log_timestamp = self.log_retriever.get_logs(self.last_log_timestamp)

    def invoke(self, memory_mb):
        self.recommendation_engine.sample(memory_mb)

    def teardown(self):
        # Just saving the Context for now.
        now = int(time.time() * 1000)
        os.makedirs(CTX_DIR, exist_ok=True)
        ctx_file = os.path.join(CTX_DIR, f"{now}.pkl")
        with open(ctx_file, "wb") as f:
            pickle.dump(self.ctx, f)
