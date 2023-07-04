import logging
import os

import numpy as np

import src.constants as const
from src.exceptions import OptimizationError
from src.exploration import AWSExplorer
from src.input_config import InputConfig
from src.recommendation import *
from src.recommendation.objectives import *


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

        memory_space = np.array(
            range(self.config.mem_bounds[0], self.config.mem_bounds[1] + 1)
        )

        self.explorer = AWSExplorer(
            lambda_name=self.config.function_name,
            payload=payload,
            max_invocation_attempts=const.MAX_NUMBER_INVOCATION_ATTEMPTS,
            aws_session=aws_session

        )

        self.param_function = ParametricFunction(
            function=lambda x, a0, a1, a2: a0 * x + a1 * np.exp(-x / a2) * x,
            bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
            execution_time_threshold=self.config.execution_time_threshold,
        )

        self.sampler = Sampler(
            explorer=self.explorer,
            memory_space=memory_space,
            explorations_count=const.DYNAMIC_SAMPLING_INITIAL_STEP,
            max_dynamic_sample_count=const.DYNAMIC_SAMPLING_MAX,
            dynamic_sampling_cv_threshold=const.TERMINATION_CV,
        )

        self.recommender = Recommender(
            objective=FitToRealCostObjective(self.param_function, memory_space),
            sampler=self.sampler,
            max_sample_count=const.TOTAL_SAMPLE_COUNT,
            termination_threshold=const.TERMINATION_THRESHOLD,
        )

    def invoke(self, memory_mb: int, parallel: int) -> list:
        durations = self.explorer.explore_parallel(parallel, parallel, memory_mb)
        print("Real cost:", self.explorer.cost)
        return durations

    def optimize(self):
        self.recommender.run()
        return self._report()

    def _report(self):
        minimum_memory, minimum_cost = self.param_function.minimize(self.sampler.memory_space)
        return {
            "Minimum Cost Memory": minimum_memory,
            "Expected Cost": minimum_cost,
            "Exploration Cost": self.explorer.cost,
        }
