import numpy as np
import scipy.stats as stats

from src.recommendation.parametric_function import ParametricFunction
from src.recommendation.objective import Objective


class FitToRealCostObjective(Objective):
    def __init__(self, param_function: ParametricFunction, memory_space: np.ndarray):
        super().__init__(param_function, memory_space)

    def get_values(self, memories: np.ndarray) -> np.ndarray:
        real_cost = self.param_function(memories)
        knowledge = self.get_knowledge(memories)
        return real_cost * knowledge

    def update_knowledge(self, memory_mb: int) -> None:
        for memory in self.knowledge_values:
            self.knowledge_values[memory] += stats.norm.pdf(
                memory, memory_mb, 200
            ) / stats.norm.pdf(memory_mb, memory_mb, 200)

    def get_knowledge(self, memories: np.ndarray) -> np.ndarray:
        knowledge = np.array([self.knowledge_values[memory] for memory in memories])
        return 1.0 + knowledge
