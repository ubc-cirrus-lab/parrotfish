from typing import Union
import boto3
import numpy as np
from google.auth import default, exceptions

from src.exploration import *
from src.logging import logger
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
        elif config.vendor == "GCP":
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
        else:
            try:
                credentials, project_id = default()
                credentials.project_id = project_id
                credentials.region = config.region
            except exceptions.DefaultCredentialsError:
                logger.critical("Failed to load Google Cloud credentials.")
                exit(1)

            self.explorer = GCPExplorer2D(
                function_name=config.function_name,
                max_invocation_attempts=config.max_number_of_invocation_attempts,
                memory_bounds=config.memory_bounds,
                credentials=credentials,
                cpu_bounds=config.cpu_bounds,
            )

        self.param_function = ParametricFunction()
        self.cpu_mem_duration_function = CpuMemDurationFunction()

        self.objective = Objective(
            param_function=self.param_function,
            memory_space=self.explorer.memory_space,
            termination_threshold=config.termination_threshold,
        ) if config.vendor != 'GCPv2' else Objective2D(
            cpu_mem_duration_function=self.cpu_mem_duration_function,
            cpu_memory_space=self.explorer.cpu_mem_space,
            termination_threshold=config.termination_threshold,
        )

        self.sampler = Sampler(
            explorer=self.explorer,
            explorations_count=config.min_sample_per_config,
            dynamic_sampling_params=config.dynamic_sampling_params,
        ) if config.vendor != 'GCPv2' else Sampler2D(
            explorer=self.explorer,
            explorations_count=config.min_sample_per_config,
            dynamic_sampling_params=config.dynamic_sampling_params,
        )

        self.recommender = Recommender(
            objective=self.objective,
            sampler=self.sampler,
            max_total_sample_count=config.max_total_sample_count,
        ) if config.vendor != 'GCPv2' else Recommender2D(
            objective=self.objective,
            sampler=self.sampler,
            max_total_sample_count=config.max_total_sample_count,
        )

    def optimize(self, apply: bool = None) -> None:
        collective_costs = np.zeros(len(self.explorer.memory_space)) if self.config.vendor != 'GCPv2' else np.zeros(len(self.explorer.cpu_mem_space))
        min_configs = []
        i = 1

        for entry in self.config.payloads:
            if len(self.config.payloads) != 1:
                print(f"Explorations for payload {i}:")
                i += 1
            # Run recommender for the specific payload
            min_configs.append(self._optimize_one_payload(entry, collective_costs))

        if len(min_configs) == 1:
            min_config = min_configs[0]
            print(f"Optimization result: {min_config} MB" if self.config.vendor != 'GCPv2' else f"Optimization result: {min_config[0]} vCPU, {min_config[1]} MB")
        else:
            for i in range(len(min_configs)):
                print(f"Optimization result for payload {i}: {min_configs[i]} MB" if self.config.vendor != 'GCPv2' else f"Optimization result for payload {i}: {min_configs[i][0]} vCPU, {min_configs[i][1]} MB")
            min_index = np.argmin(collective_costs)
            min_config = self.explorer.memory_space[min_index] if self.config.vendor != 'GCPv2' else self.explorer.cpu_mem_space[min_index]
            print(f"Optimization result of the average cost: {min_config} MB" if self.config.vendor != 'GCPv2' else f"Optimization result of the average cost: {min_config[0]} vCPU, {min_config[1]} MB")

        if apply:
            self._apply_configuration(min_config)
        else:
            self.explorer.config_manager.reset_config()

    def _optimize_one_payload(self, entry: dict, collective_costs: np.ndarray) -> any:
        self.explorer.payload = entry["payload"]
        self.recommender.run()
        collective_costs += (
            self.param_function(self.explorer.memory_space) * entry["weight"]
        ) if self.config.vendor != 'GCPv2' else (
            self.cpu_mem_duration_function((self.explorer.cpu_mem_space[:, 0], self.explorer.cpu_mem_space[:, 1])) * entry["weight"]
        )
        if self.config.vendor != 'GCPv2':
            minimum_memory = self.param_function.minimize(
                self.explorer.memory_space, self.config.constraint_execution_time_threshold, self.config.constraint_cost_tolerance_percent
            )
        else:
            [min_cpu, min_mem] = self.cpu_mem_duration_function.minimize(
                self.explorer.cpu_mem_space, self.config.constraint_execution_time_threshold, self.config.constraint_cost_tolerance_percent
            )
        self.objective.reset()
        return minimum_memory if self.config.vendor != 'GCPv2' else [min_cpu, min_mem]

    def _apply_configuration(self, configuration: Union[int, list]):
        if self.config.vendor != 'GCPv2':
            self.explorer.config_manager.set_config(
                configuration, self.explorer.config_manager.initial_config.timeout
            )
        else:
            self.explorer.config_manager.set_config(
                memory_mb=configuration[1], 
                timeout=self.explorer.config_manager.initial_config.timeout, 
                cpu=configuration[0],
            )
