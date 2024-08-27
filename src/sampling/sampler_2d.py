import math

import numpy as np

from src.exception import *
from src.exploration import *
from src.logger import logger
from .data_point_2d import DataPoint2D
from .sample_2d import Sample2D


class Sampler2D:
    def __init__(
        self,
        explorer: Explorer2D,
        explorations_count: int,
        dynamic_sampling_params: dict,
    ):
        self.sample = None
        self.explorer = explorer
        self.cpu_mem_space = explorer.cpu_mem_space
        self._explorations_count = explorations_count
        self._dynamic_sampling_params = dynamic_sampling_params

    def initialize_sample(self) -> None:
        """Initializes the sample by exploring with 3 memory values from the memory space.

        Raises:
            SamplingError: If an error occurred while sampling.
        """
        self.sample = Sample2D()

        self._sample_first_memory_config()

        # we are initially indexing the cpu-memory space at five indices
        index = math.ceil(len(self.cpu_mem_space) / 5)

        for [cpu, memory] in [self.cpu_mem_space[index], self.cpu_mem_space[index*2], self.cpu_mem_space[index*3], self.cpu_mem_space[-1]]:
            try:
                self.update_sample(cpu, memory)

            except SamplingError as e:
                logger.debug(e)
                raise

    def _sample_first_memory_config(self):
        while len(self.cpu_mem_space) >= 5:
            try:
                self.update_sample(float(self.cpu_mem_space[0][0]), int(self.cpu_mem_space[0][1]))

            except FunctionENOMEM:
                logger.info(f"ENOMEM: trying with new memories")
                self.cpu_mem_space = np.array(
                    [
                        [cpu, mem]
                        for [cpu, mem] in self.cpu_mem_space
                        if mem >= self.cpu_mem_space[0][1] + 128 and cpu >= self.cpu_mem_space[0][0] + 0.08
                    ]
                )

            except SamplingError as e:
                logger.debug(e)
                raise

            else:
                break

        if len(self.cpu_mem_space) <= 5:
            raise NoMemoryLeftError

    def update_sample(self, cpu: float, memory_mb: int) -> None:
        """Updates the sample by invoking the serverless function with memory size configuration @memory_mb, vcpu size configuration @cpu 
        and appending the results to the sample.

        Args:
            cpu (float): vCPU size configuration.
            memory_mb (int): Memory size configuration in MB.

        Raises:
            SamplingError: If an error occurred while sampling.
        """
        logger.info(f"Sampling: cpu {cpu}, memory {memory_mb} MB.")
        try:
            subsample_durations = self.explorer.explore_parallel(
                nbr_invocations=self._explorations_count,
                nbr_threads=self._explorations_count,
                cpu = cpu,
                memory_mb=memory_mb,
            )
        except ExplorationError as e:
            logger.debug(e)
            raise

        subsample_durations = self._explore_dynamically(durations=subsample_durations)

        subsample = [DataPoint2D(cpu, memory_mb, result) for result in subsample_durations]
        self.sample.update(subsample)

        logger.info(
            f"Finished sampling cpu {cpu}, memory {memory_mb} with billed duration results: {subsample_durations} in ms."
        )

    def _explore_dynamically(self, durations: list) -> list:
        """Samples dynamically until the invocations results are consistent enough. Consistency is measured by the
        coefficient of variation.

        Args:
            durations (list): List of the initial sample's durations.

        Returns:
            list: List of sample datapoints' durations.

        Raises:
            SamplingError: If an error occurred while invoking or exploration price calculation.
            ValueError: If the @durations length is less than the initial samples count.
        """

        if len(durations) < self._explorations_count:
            raise ValueError(
                f"Length of the input {durations} is less than {self._explorations_count}"
            )

        dynamic_sample_count = 0
        min_cv = np.std(durations, ddof=1) / np.mean(durations)

        while (
            dynamic_sample_count < self._dynamic_sampling_params["max_sample_per_config"]
            and min_cv
            > self._dynamic_sampling_params["coefficient_of_variation_threshold"]
        ):
            try:
                result = self.explorer.explore()

            except ExplorationError as e:
                logger.debug(e)
                raise

            dynamic_sample_count += 1

            # Choose the sample from durations that minimizes coefficient of variation.
            values = durations.copy()
            for i in range(len(durations)):
                value = values[i]
                values[i] = result
                coefficient_variation = np.std(values, ddof=1) / np.mean(values)
                if min_cv > coefficient_variation:
                    min_cv = coefficient_variation
                    durations = values.copy()
                values[i] = value

        return durations
