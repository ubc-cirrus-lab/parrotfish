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
        self.path: str = config_dir
        self.workload_file_path = os.path.join(config_dir, "workload.json")
        self.config_file_path = os.path.join(config_dir, "config.json")
        self.payload_file_path = os.path.join(config_dir, "payload.json")

        # TODO: implement checkpoint & restore on Context (loading from pickle?).
        self.ctx = Context()

        with open(self.config_file_path) as f:
            self.config: BenchmarkConfig = BenchmarkConfig(f)

        self.last_log_timestamp = None

        # Instantiate SPOT system components
        self.price_retriever = AWSPriceRetriever(self.ctx, self.config.region)
        self.log_retriever = AWSLogRetriever(
            self.ctx, aws_session, self.config.function_name
        )
        function_invoker = AWSLambdaInvoker(
            self.ctx, aws_session, self.config.function_name
        )
        self.recommendation_engine = RecommendationEngine(
            function_invoker, self.payload_file_path, self.config.mem_bounds
        )
        self.benchmark_name = os.path.basename(config_dir)

    def optimize(self):
        final_df = self.recommendation_engine.run()
        self.ctx.save_final_result(final_df)
        return final_df

    def collect_data(self):
        # retrieve latest config, logs, pricing scheme
        self.price_retriever.fetch_current_pricing()
        self.last_log_timestamp = self.log_retriever.get_logs(self.last_log_timestamp)

    def invoke(self, memory_mb, count):
        for _ in range(count):
            self.recommendation_engine.invoke_once(memory_mb)

    def teardown(self, optimization_s):
        # Just saving the Context for now.
        os.makedirs(CTX_DIR, exist_ok=True)
        ctx_file = os.path.join(
            CTX_DIR, f"{self.benchmark_name}_{int(time.time() * 1000)}.pkl"
        )
        with open(ctx_file, "wb") as f:
            self.ctx.save_supplemantary_info(self.config.function_name, optimization_s)
            pickle.dump(self.ctx, f)
