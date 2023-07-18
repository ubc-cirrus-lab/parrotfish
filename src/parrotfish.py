import sys

import boto3
import numpy as np
from google.auth import default, exceptions

from src.exploration import *
from src.recommendation import *
from src.recommendation.objectives import *


class Parrotfish:
    def __init__(self, config: any):

        self.payloads = config.payloads if config.hasattr("payloads") else None

        if config.vendor == "AWS":
            self.explorer = AWSExplorer(
                lambda_name=config.function_name,
                payload=config.payload,
                max_invocation_attempts=config.max_number_of_invocation_attempts,
                memory_bounds=config.memory_bounds,
                aws_session=boto3.Session(region_name=config.region),
            )
        else:
            try:
                credentials, project_id = default()
                credentials.project_id = project_id
                credentials.region = config.region
            except exceptions.DefaultCredentialsError:
                print("Failed to load Google Cloud credentials.", file=sys.stderr)
                exit(1)

            self.explorer = GCPExplorer(
                function_name=config.function_name,
                payload=config.payload,
                memory_bounds=config.memory_bounds,
                credentials=credentials,
            )

        self.param_function = ParametricFunction(
            function=lambda x, a0, a1, a2: a0 * x + a1 * np.exp(-x / a2) * x,
            bounds=([0, 0, 0], [np.inf, np.inf, np.inf]),
            execution_time_threshold=config.execution_time_threshold,
        )

        sampler = Sampler(
            explorer=self.explorer,
            explorations_count=config.number_invocations,
            max_dynamic_sample_count=config.max_dynamic_sample_size,
            dynamic_sampling_cv_threshold=config.dynamic_sampling_termination_threshold,
        )

        objective = FitToRealCostObjective(
            param_function=self.param_function,
            memory_space=self.explorer.memory_space,
            termination_threshold=config.termination_threshold,
        )

        self.recommender = Recommender(
            objective=objective,
            sampler=sampler,
            max_sample_count=config.sample_size,
        )

    def invoke(self, memory_mb: int, parallel: int) -> list:
        durations = self.explorer.explore_parallel(parallel, parallel, memory_mb)
        print("Real cost:", self.explorer.cost)
        return durations

    def optimize(self):
        self.recommender.run()
        return self._report()

    def optimize_weighted(self):
        collective_costs = np.array([])
        for entry in self.payloads:
            self.explorer.payload = entry.payload
            self.recommender.run()
            collective_costs += self.param_function(self.explorer.memory_space) * entry.weight
            self.param_function.params = None
        weighted_costs = collective_costs / len(self.payloads)
        min_index = np.argmin(weighted_costs)
        min_memory = weighted_costs[min_index]
        min_cost = weighted_costs[min_index]
        return {
            "Minimum Cost Memory": min_memory,
            "Expected Cost": min_cost,
            "Exploration Cost": self.explorer.cost,
        }

    def _report(self):
        minimum_memory, minimum_cost = self.param_function.minimize(
            self.explorer.memory_space
        )
        return {
            "Minimum Cost Memory": minimum_memory,
            "Expected Cost": minimum_cost,
            "Exploration Cost": self.explorer.cost,
        }
