import numpy as np
import scipy.stats as stats

from .parametric_function import ParametricFunction


class Objective:
    def __init__(
        self,
        param_function: ParametricFunction,
        memory_space: np.ndarray,
        termination_threshold: float,
    ):
        self.param_function = param_function
        self.memory_space = memory_space
        self.knowledge_values = {x: 0 for x in memory_space}
        self.termination_threshold = termination_threshold

    @property
    def termination_value(self) -> float:
        """computes a value that indicates that we are confident"""
        knowledge_values = self.get_knowledge(self.memory_space)
        y = self.param_function(self.memory_space) * self.memory_space
        return knowledge_values[np.argmin(y)]

    def get_values(self, memories: np.ndarray) -> np.ndarray:
        """Computes the objective values of the memories in input."""
        real_cost = self.param_function(memories) * memories
        knowledge = self.get_knowledge(memories)
        return real_cost * knowledge

    def update_knowledge(self, memory_mb: int) -> None:
        """Updates the knowledge values of the memory in input."""
        for memory in self.knowledge_values:
            self.knowledge_values[memory] += stats.norm.pdf(
                memory, memory_mb, 200
            ) / stats.norm.pdf(memory_mb, memory_mb, 200)

    def get_knowledge(self, memories: np.ndarray) -> np.ndarray:
        """Returns the knowledge values of the memories in input."""
        knowledge = np.array([self.knowledge_values[memory] for memory in memories])
        return 1.0 + knowledge

    def reset(self) -> None:
        """Resets the knowledge values and parametric function."""
        self.param_function.params = None
        self.knowledge_values = {x: 0 for x in self.memory_space}
