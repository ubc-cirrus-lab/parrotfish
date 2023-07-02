import numpy as np
import scipy.stats as stats

from src.data_model import *
from src.recommendation.objective import Objective


class FitToRealCostObjective(Objective):
    def __init__(self, param_function: ParametricFunction, memory_space: np.ndarray):
        super().__init__(param_function, memory_space)

    def get_values(self, memories: np.ndarray) -> np.ndarray:
        real_cost = self.param_function(memories)
        knowledge = self.get_knowledge(memories)
        return real_cost * knowledge

    def update_knowledge(self, memory_mb):
        for memory in self.knowledge_values:
            self.knowledge_values[memory] += stats.norm.pdf(memory, memory_mb, 200) / stats.norm.pdf(memory_mb, memory_mb, 200)

    def get_knowledge(self, x):
        if isinstance(x, np.ndarray) or isinstance(x, list):
            knowledge = np.array([self.knowledge_values[xs] for xs in x])
        else:
            knowledge = self.knowledge_values[x]
        # Here we add 1.0 because we don't want the memory values we didn't explore to be 0 that will make
        # cost * knowledge 0, if 0 it's only the cost which matters, knowledge is like a penalty for the sample.
        return 1.0 + knowledge
