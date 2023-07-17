import logging

import numpy as np

from .objective import Objective
from .sampler import Sampler
from ..exceptions import *


class Recommender:
    def __init__(
        self,
        objective: Objective,
        sampler: Sampler,
        max_sample_count: int,
    ):
        self.objective = objective
        self.sampler = sampler
        self._max_sample_count = max_sample_count
        self._logger = logging.getLogger(__name__)

    @property
    def _is_termination_reached(self) -> bool:
        """Check if the termination condition is reached.

        Returns:
           bool: True if the termination condition is reached, False otherwise.
        """
        sample_count = len(self.sampler.sample)
        termination_value = self.objective.termination_value
        return (
            sample_count > self._max_sample_count
            or termination_value < self.objective.termination_threshold
        )

    def run(self):
        """Runs the recommender algorithm.

        Raises:
            OptimizationError: If an error occurred while running the recommender algorithm.

        This method initializes the recommender, and then iteratively samples (adaptive sampling), and updates the
        objective knowledge values and the parametric function until the termination condition is reached.
        """
        self._initialize()
        while not self._is_termination_reached:
            memory = self._choose_memory_to_explore()
            self._update(memory)

    def _initialize(self):
        """Initializes the sample, objective knowledge, and parametric function.

        Raises:
            OptimizationError: If an error occurred while fitting the parametric function.

        This method initializes the sample by drawing samples from the memory space.
        It updates the knowledge values for each sampled memory and fits the parametric function.
        """
        self.sampler.initialize_sample()

        # update the knowledge values for each sampled memory.
        sample = self.sampler.sample
        for memory in set(sample.memories):
            self.objective.update_knowledge(memory)
        try:
            self.objective.param_function.fit(sample)
        except RuntimeError as e:
            self._logger.error(e.args[0])
            raise OptimizationError(e.args[0])

    def _update(self, memory_mb: int):
        """Updates the sample, knowledge values, and parametric function.

        Args:
            memory_mb (int): The memory value to explore with in MB.

        Raises:
            SamplingError: If an error occurred while sampling.

        This method updates the sample by exploring with the given memory value and then update the sample with the new
        datapoints, then it updates the knowledge values for the given memory, and fits the parametric function.
        """
        self.sampler.update_sample(memory_mb)
        self.objective.update_knowledge(memory_mb)
        try:
            self.objective.param_function.fit(self.sampler.sample)
        except RuntimeError as e:
            self._logger.error(e.args[0])
            raise OptimizationError(e.args[0])

    def _choose_memory_to_explore(self) -> int:
        """Chooses the memory size configuration to explore with from the remainder memories in the memory space.

        Returns:
            int: Memory value in the remainder memories that minimizes the objective.

        Raises:
            NoMemoryLeftError: If no memory is left to explore with.
        """
        # compute the memories we can explore from.
        sample_memories = set(self.sampler.sample.memories)
        memory_space = self.sampler.memory_space
        remainder_memories = np.array(
            [memory for memory in memory_space if memory not in sample_memories],
            dtype=int,
        )

        if len(remainder_memories) == 0:
            raise NoMemoryLeftError

        # return the memory that minimizes the objective.
        values = self.objective.get_values(remainder_memories)
        return remainder_memories[np.argmin(values)]
