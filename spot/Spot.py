import time
import os
import numpy as np
import pandas as pd
from spot.prices.aws_price_retriever import AWSPriceRetriever
from spot.logs.aws_log_retriever import AWSLogRetriever
from spot.invocation.aws_lambda_invoker import AWSLambdaInvoker
from spot.context import Context
from spot.benchmark_config import BenchmarkConfig
from spot.recommendation_engine.recommendation_engine import RecommendationEngine
from spot.recommendation_engine.utility import Utility
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
            function_invoker, self.payload_file_path, self.config.mem_bounds, self.config.execution_time_threshold
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

    def invoke(self, memory_mb, count, force):
        if force:
            cached_duration = None
        else:
            cached_duration = self._cached_duration(memory_mb, count)

        if cached_duration is None:
            billed_duration = np.arange(count, dtype=np.double)
            for i in range(count):
                df = self.recommendation_engine.invoke_once(memory_mb, is_warm=(i > 0))
                billed_duration[i] = df["Billed Duration"][0]
            print(
                "Real cost:", Utility.calculate_cost(billed_duration, memory_mb).mean()
            )
        else:
            print("cache hit!")
            result_df = pd.DataFrame(
                {
                    "Duration": [cached_duration]
                    * count,  # TODO: fill in Duration instead of Billed Duration
                    "Max Memory Used": [cached_duration]
                    * count,  # TODO: fill in Max Memory Used instead of Billed Duration
                    "Billed Duration": [cached_duration] * count,
                    "Memory Size": [memory_mb] * count,
                }
            )
            self.ctx.save_invocation_result(result_df)
            print(
                "Real cost:", Utility.calculate_cost(cached_duration, memory_mb).mean()
            )

    def teardown(self, optimization_s):
        # Just saving the Context for now.
        os.makedirs(CTX_DIR, exist_ok=True)
        ctx_file = os.path.join(
            CTX_DIR, f"{self.benchmark_name}_{int(time.time() * 1000)}.pkl"
        )
        self.ctx.save_context(self.config.function_name, ctx_file, optimization_s)

    def _cached_duration(self, mem, count):
        cached_data = self.ctx.cached_data()
        if cached_data is None:
            return None
        cached_function_data = cached_data[
            (cached_data["function_name"].str.contains(self.config.nickname))
            & (cached_data["memory"] == mem)
        ]
        if len(cached_function_data) < count:
            return None
        return cached_function_data["duration"].mean()
