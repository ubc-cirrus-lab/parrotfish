import logging
import os

import numpy as np
import pandas as pd

from src.data_model import *
from src.exceptions import *
from src.exploration import AWSExplorer
from src.input_config import InputConfig
from src.recommendation import Recommender
from src.recommendation.objectives import *
from src.recommendation.sampler import Sampler
import src.constants as const


class Spot:
    def __init__(self, config_dir: str, aws_session):
        self._logger = logging.getLogger(__name__)

        # Load configuration values from config.json
        config_file_path = os.path.join(config_dir, "config.json")
        payload_file_path = os.path.join(config_dir, "payload.json")

        with open(payload_file_path) as f:
            payload = f.read()

        with open(config_file_path) as f:
            self.config: InputConfig = InputConfig(f)

        memory_space = np.array(range(self.config.mem_bounds[0], self.config.mem_bounds[1] + 1))

        self.explorer = AWSExplorer(self.config.function_name, payload, const.DYNAMIC_SAMPLING_INITIAL_STEP, aws_session)

        self.param_function = ParametricFunction(
            function=lambda x, a0, a1, a2: a0 * x + a1 * np.exp(-x / a2) * x,
            params=[1000, 10000, 100],
            bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
            execution_time_threshold=self.config.execution_time_threshold
        )

        self.sampler = Sampler(
            explorer=self.explorer,
            memory_space=memory_space,
            explorations_count=const.DYNAMIC_SAMPLING_INITIAL_STEP,
            max_dynamic_sample_count=const.DYNAMIC_SAMPLING_MAX,
            termination_threshold=const.TERMINATION_CV
        )

        self.recommendation_engine = Recommender(
            objective=FitToRealCostObjective(self.param_function, memory_space),
            sampler=self.sampler,
            max_sample_count=const.TOTAL_SAMPLE_COUNT,
            termination_threshold=const.TERMINATION_THRESHOLD,
        )

        self.benchmark_name = os.path.basename(config_dir)

    def optimize(self):
        try:
            self.recommendation_engine.run()
        except OptimizationError as e:
            self._logger.error(e)
            exit(1)
        return self.report()

    def invoke(self, memory_mb: int, parallel: int) -> list:
        durations = self.explorer.explore_parallel(parallel, parallel, memory_mb)
        print("Real cost:", self.explorer.cost)
        return durations

    def report(self):
        try:
            minimum_memory, minimum_cost = self.param_function.minimize(self.sampler.memory_space)
            result = {
                "Minimum Cost Memory": [minimum_memory],
                "Expected Cost": [minimum_cost],
                "Exploration Cost": [self.explorer.cost],
            }
            return pd.DataFrame.from_dict(result)

        except NoMemoryLeftError:
            print("No memory configuration is possible. The execution time threshold is too low!")
            exit(1)
