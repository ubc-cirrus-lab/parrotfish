import numpy as np
import scipy.stats as stats
from .cpu_mem_duration_function import CpuMemDurationFunction

class Objective2D:
    def __init__(
        self,
        cpu_mem_duration_function: CpuMemDurationFunction,
        cpu_memory_space: np.ndarray, # The format is [[cpu_1, mem_1], ...]
        termination_threshold: float,
    ):
        self.cpu_mem_duration_function = cpu_mem_duration_function
        self.cpu_memory_space = cpu_memory_space
        # Create a dictionary where keys are (cpu, memory) tuples and values are the belief values
        self.knowledge_values = {
            (c, m): 0 for [c, m] in cpu_memory_space
        }
        self.termination_threshold = termination_threshold

    @property
    def termination_value(self) -> float:
        """Computes a value that indicates that we are confident."""
        knowledge_values = self.get_knowledge(self.cpu_memory_space)
        y = self.cpu_mem_duration_function((self.cpu_memory_space[:, 0], self.cpu_memory_space[:, 1])) * (self.cpu_memory_space[:, 0] * 0.00002400 + self.cpu_memory_space[:, 1] * 0.00000250 / 1024)
        return knowledge_values[np.argmin(y)]

    def get_values(self, cpu_memories: np.ndarray) -> np.ndarray:
        """Computes the objective values of the cpu/memory combinations in input."""
        real_cost = self.cpu_mem_duration_function((cpu_memories[:, 0], cpu_memories[:, 1])) * (cpu_memories[:, 0] * 0.00002400 + cpu_memories[:, 1] * 0.00000250 / 1024)
        knowledge = self.get_knowledge(cpu_memories)
        return real_cost * knowledge

    def update_knowledge(self, cpu_value: float, memory_mb: int) -> None:
        """Updates the knowledge values of the cpu/memory combination in input."""
        for (cpu, memory) in self.knowledge_values:
            self.knowledge_values[(cpu, memory)] += stats.multivariate_normal.pdf(
                [cpu, memory], [cpu_value, memory_mb], [[0.2**2, 0], [0, 400**2]]
            ) / stats.multivariate_normal.pdf(
                [cpu_value, memory_mb], [cpu_value, memory_mb], [[0.2**2, 0], [0, 400**2]]
            )

    def get_knowledge(self, cpu_mem_space: np.ndarray) -> np.ndarray:
        """Returns the knowledge values of the cpu/memory combinations in input."""
        knowledge = np.array([self.knowledge_values[(c, m)] for [c, m] in cpu_mem_space])
        return 1.0 + knowledge
    
    def reset(self) -> None:
        """Resets the knowledge values and parametric function."""
        self.cpu_mem_duration_function.params = None
        self.knowledge_values = {
            (c, m): 0 for [c, m] in self.cpu_memory_space
        }
