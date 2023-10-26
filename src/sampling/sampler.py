import math

import numpy as np

from src.exception import *
from src.exploration import *
from src.logging import logger
from .data_point import DataPoint
from .sample import Sample


class Sampler:
    def __init__(
        self,
        explorer: Explorer,
        explorations_count: int,
        dynamic_sampling_params: dict,
    ):
        self.sample = None
        self.explorer = explorer
        self.memory_space = explorer.memory_space
        self._explorations_count = explorations_count
        self._dynamic_sampling_params = dynamic_sampling_params

    def initialize_sample(self) -> None:
        """Initializes the sample by exploring with 3 memory values from the memory space.

        Raises:
            SamplingError: If an error occurred while sampling.
        """
        self.sample = Sample()

        self._sample_first_memory_config()

        # we are interested to sample more in the third part of the memory space.
        index = math.ceil(len(self.memory_space) / 3)

        for memory in [self.memory_space[index], self.memory_space[-1]]:
            try:
                self.update_sample(memory)

            except SamplingError as e:
                logger.debug(e)
                raise

    def _sample_first_memory_config(self):
        while len(self.memory_space) >= 3:
            try:
                self.update_sample(int(self.memory_space[0]))

            except FunctionENOMEM:
                logger.info(f"ENOMEM: trying with new memories")
                self.memory_space = np.array(
                    [
                        mem
                        for mem in self.memory_space
                        if mem >= self.memory_space[0] + 128
                    ],
                    dtype=int,
                )

            except SamplingError as e:
                logger.debug(e)
                raise

            else:
                break

        if len(self.memory_space) <= 3:
            raise NoMemoryLeftError

    def update_sample(self, memory_mb: int) -> None:
        """Updates the sample by invoking the serverless function with memory size configuration @memory_mb and
        appending the results to the sample.

        Args:
            memory_mb (int): Memory size configuration in MB.

        Raises:
            SamplingError: If an error occurred while sampling.
        """
        logger.info(f"Sampling: {memory_mb} MB.")
        try:
            subsample_durations = self.explorer.explore_parallel(
                nbr_invocations=self._explorations_count,
                nbr_threads=self._explorations_count,
                memory_mb=memory_mb,
            )
        except ExplorationError as e:
            logger.debug(e)
            raise

        subsample_durations = self._explore_dynamically(durations=subsample_durations)

        subsample = [DataPoint(memory_mb, result) for result in subsample_durations]
        self.sample.update(subsample)

        logger.info(
            f"Finished sampling {memory_mb} with billed duration results: {subsample_durations} in ms."
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
