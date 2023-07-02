from abc import ABC, abstractmethod

import numpy as np

from src.data_model import *


class Objective(ABC):
    def __init__(self, param_function: ParametricFunction, memory_space: np.ndarray):
        self.param_function = param_function
        self.memory_space = memory_space
        self.knowledge_values = {x: 0 for x in memory_space}

    @property
    def termination_value(self):
        knowledge_values = self.get_knowledge(self.memory_space)
        y = self.param_function(np.array(self.memory_space))
        return knowledge_values[np.argmin(y)]

    @abstractmethod
    def get_values(self, memories: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def update_knowledge(self, memories: int or list):
        pass

    @abstractmethod
    def get_knowledge(self, x):
        pass
