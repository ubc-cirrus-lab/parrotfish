from abc import ABC, abstractmethod

import numpy as np

from .parametric_function import ParametricFunction


class Objective(ABC):
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
    @abstractmethod
    def termination_value(self) -> float:
        """computes a value that indicates that we are confident"""
        pass

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
