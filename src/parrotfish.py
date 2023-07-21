import sys

import boto3
import numpy as np
from google.auth import default, exceptions

from src.exploration import *
from src.recommendation import *
from src.recommendation.objectives import *


class Parrotfish:
    def __init__(self, config: any):
        self.payloads = config.payloads if hasattr(config, "payloads") else None

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

    def optimize(self) -> dict:
        if not self.payloads:
            self.recommender.run()
            minimum_memory = self.param_function.minimize(
                self.explorer.memory_space
            )

        else:
            minimum_memory = self._optimize_multiple_payloads()

        return {
            "Minimum Cost Memory": minimum_memory,
            "Exploration Cost": self.explorer.cost,
        }

    def _optimize_multiple_payloads(self) -> int:
        collective_costs = np.zeros(len(self.explorer.memory_space))

        for entry in self.payloads:
            # Run recommender for the specific payload
            self.explorer.payload = entry["payload"]
            self.recommender.run()
            collective_costs += self.param_function(self.explorer.memory_space) * entry["weight"]
            # Reset the parametric function and the objective.
            self.param_function.params = None
            self.recommender.objective.knowledge_values = {x: 0 for x in self.explorer.memory_space}

        average_weighted_costs = collective_costs / len(self.payloads)
        min_index = np.argmin(average_weighted_costs)
        return self.explorer.memory_space[min_index]
