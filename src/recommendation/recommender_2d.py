import numpy as np

from src.objective import Objective2D
from src.sampling import Sampler2D
from ..exception import *
from ..logger import logger


class Recommender2D:
    def __init__(
        self,
        objective: Objective2D,
        sampler: Sampler2D,
        max_total_sample_count: int,
    ):
        self.objective = objective
        self.sampler = sampler
        self._max_total_sample_count = max_total_sample_count

    @property
    def _is_termination_reached(self) -> bool:
        """Check if the termination condition is reached.

        Returns:
           bool: True if the termination condition is reached, False otherwise.
        """
        sample_count = len(self.sampler.sample)
        termination_value = self.objective.termination_value
        return (
            sample_count > self._max_total_sample_count
            or termination_value > self.objective.termination_threshold
        )

    def run(self):
        """Runs the recommender algorithm.

        Raises:
            OptimizationError: If an error occurred while running the recommender algorithm.

        This method initializes the recommender, and then iteratively samples (adaptive sampling), and updates the
        objective knowledge values and the CPU-Memory-Duration function until the termination condition is reached.
        """
        self._initialize()
        while not self._is_termination_reached:
            cpu, memory = self._choose_cpu_memory_to_explore()
            self._update(cpu, memory)

    def _initialize(self):
        """Initializes the sample, objective knowledge, and CPU-Memory-Duration function.

        Raises:
            OptimizationError: If an error occurred while fitting the CPU-Memory-Duration function.

        This method initializes the sample by drawing samples from the cpu memory space.
        It updates the knowledge values for each sampled cpu & memory and fits the CPU-Memory-Duration function.
        """
        self.sampler.initialize_sample()

        # update the knowledge values for each sampled cpu & memory.
        sample = self.sampler.sample
        for [cpu, memory] in set(tuple(row) for row in sample.cpu_mems):
            self.objective.update_knowledge(cpu, memory)

        try:
            self.objective.cpu_mem_duration_function.fit(sample)
        except RuntimeError as e:
            logger.debug(e.args[0])
            raise OptimizationError(e.args[0])

    def _update(self, cpu: float, memory_mb: int):
        """Updates the sample, knowledge values, and CPU-Memory-Duration function.

        Args:
            cpu (float): The cpu value to explore in vCPU.
            memory_mb (int): The memory value to explore with in MB.

        Raises:
            SamplingError: If an error occurred while sampling.

        This method updates the sample by exploring with the given cpu and memory value and then update the sample with the new
        datapoints, then it updates the knowledge values for the given memory, and fits the CPU-Memory-Duration function.
        """
        self.sampler.update_sample(cpu, memory_mb)
        self.objective.update_knowledge(cpu, memory_mb)
        try:
            self.objective.cpu_mem_duration_function.fit(self.sampler.sample)
        except RuntimeError as e:
            logger.debug(e.args[0])
            raise OptimizationError(e.args[0])

    def _choose_cpu_memory_to_explore(self) -> list[float, int]:
        """Chooses the cpu and memory size configuration to explore with from the remainder cpu memorie combinations in the cpu memory space.

        Returns:
            float, int: CPU and Memory values in the remainder CPU memorie combinations that minimizes the objective.

        Raises:
            NoMemoryLeftError: If no CPU or memory is left to explore with.
        """
        # compute the CPU and memories we can explore from.
        sample_cpu_memories = set(tuple(row) for row in self.sampler.sample.cpu_mems)
        cpu_memory_space = self.sampler.cpu_mem_space
        remainder_cpu_memories = np.array(
            [[cpu, mem] for (cpu, mem) in cpu_memory_space if (cpu, mem) not in sample_cpu_memories],
        )
        if len(remainder_cpu_memories) == 0:
            raise NoMemoryLeftError

        # return the cpu and memory configuration that minimizes the objective.
        values = self.objective.get_values(remainder_cpu_memories)
        return remainder_cpu_memories[np.argmin(values)]
