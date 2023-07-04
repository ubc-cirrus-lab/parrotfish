from abc import ABC, abstractmethod

import numpy as np

from .parametric_function import ParametricFunction


class Objective(ABC):
    def __init__(self, param_function: ParametricFunction, memory_space: list):
        self.param_function = param_function
        self.memory_space = np.array(memory_space)
        self.knowledge_values = {x: 0 for x in memory_space}

    @property
    def termination_value(self):
        knowledge_values = self.get_knowledge(self.memory_space)
        y = self.param_function(self.memory_space)
        return knowledge_values[np.argmin(y)]

    @abstractmethod
    def get_values(self, memories: np.ndarray) -> np.ndarray:
        """Computes the objective values of the memories in input."""
        pass

    @abstractmethod
    def update_knowledge(self, memory: int) -> None:
        """Updates the knowledge values of the memory in input."""
        pass

    @abstractmethod
    def get_knowledge(self, memories: np.ndarray) -> np.ndarray:
        """Returns the knowledge values of the memories in input."""
        pass
