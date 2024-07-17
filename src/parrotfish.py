import boto3
import numpy as np
from google.auth import default, exceptions

from src.exploration import *
from src.logger import logger
from src.objective import *
from src.recommendation import *
from src.sampling import *


class Parrotfish:
    def __init__(self, config: any):
        self.config = config

        if config.vendor == "AWS":
            self.explorer = AWSExplorer(
                lambda_name=config.function_name,
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
                logger.critical("Failed to load Google Cloud credentials.")
                exit(1)

            self.explorer = GCPExplorer(
                function_name=config.function_name,
                max_invocation_attempts=config.max_number_of_invocation_attempts,
                memory_bounds=config.memory_bounds,
                credentials=credentials,
            )

        self.param_function = ParametricFunction()

        self.objective = Objective(
            param_function=self.param_function,
            memory_space=self.explorer.memory_space,
            termination_threshold=config.termination_threshold,
        )

        self.sampler = Sampler(
            explorer=self.explorer,
            explorations_count=config.min_sample_per_config,
            dynamic_sampling_params=config.dynamic_sampling_params,
        )

        self.recommender = Recommender(
            objective=self.objective,
            sampler=self.sampler,
            max_total_sample_count=config.max_total_sample_count,
        )

    def optimize(self, apply: bool = None) -> int:
        collective_costs = np.zeros(len(self.explorer.memory_space))
        min_memories = []
        i = 1

        for entry in self.config.payloads:
            if len(self.config.payloads) != 1:
                print(f"Explorations for payload {i}:")
                i += 1
            # Run recommender for the specific payload
            min_memories.append(self._optimize_one_payload(entry, collective_costs))

        if len(min_memories) == 1:
            minimum_memory = min_memories[0]
            print(f"Optimization result: {minimum_memory} MB")
        else:
            for i in range(len(min_memories)):
                print(f"Optimization result for payload {i}: {min_memories[i]} MB")
            min_index = np.argmin(collective_costs)
            minimum_memory = self.explorer.memory_space[min_index]
            print(f"Optimization result of the average cost: {minimum_memory} MB")

        if apply:
            self._apply_configuration(minimum_memory)
        else:
            self.explorer.config_manager.reset_config()

        return minimum_memory

    def _optimize_one_payload(self, entry: dict, collective_costs: np.ndarray) -> int:
        self.explorer.payload = entry["payload"]
        self.objective.reset()
        self.recommender.run()
        collective_costs += (
                self.param_function(self.explorer.memory_space) * entry["weight"]
        )
        minimum_memory = self.param_function.minimize(
            self.explorer.memory_space, self.config.constraint_execution_time_threshold,
            self.config.constraint_cost_tolerance_percent
        )
        return minimum_memory

    def _apply_configuration(self, memory_mb: int):
        self.explorer.config_manager.set_config(
            memory_mb, self.explorer.config_manager.initial_config.timeout
        )
