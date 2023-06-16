from . import Objective
import spot.constants as const
import numpy as np
from scipy import stats
from spot.data_model import *


class NormalObjective(Objective):
    # This class gives poor results better use FitToRealCostObjective
    def __init__(self, fitting_function: FittingFunction, memory_range: list):
        super().__init__(fitting_function, memory_range)
        self.knowledge_values = {
            x: 0 for x in range(self.memory_range[0], self.memory_range[1] + 1)
        }
        self.ratio = 1

    def normalized_cost(self, x):
        # Normalizing the cost so that ALPHA * normalized_cost will have a meaning
        return self.fitting_function(x) * x / self._min_cost()

    def _min_cost(self):
        # This function is only to be used by normalized_cost
        min_cost = np.inf
        for memory_value in range(self.memory_range[0], self.memory_range[1] + 1):
            cost = self.fitting_function(memory_value) * memory_value

            if cost < min_cost:
                min_cost = cost
        return min_cost

    def get_value(self, x):
        return self.knowledge_values[x] + const.ALPHA * self.normalized_cost(x) # here we care about the cost because we want better exploration time.

    def update_knowledge(self, x):
        for key in self.knowledge_values:
            self.knowledge_values[key] += self.get_normal_value(key, x, const.NORMAL_SCALE)
        self.ratio *= 1 / sum(list(self.knowledge_values.values()))
        self.normalize()

    def get_normal_value(self, x, mean, std):
        return self.ratio * stats.norm.pdf(x, mean, std)

    def normalize(self):
        knowledge = self.knowledge_values
        sum = np.sum(list(knowledge.values()))
        for k in knowledge:
            knowledge[k] /= sum

    def get_knowledge(self, x):
        if isinstance(x, np.ndarray):
            knowledge = np.array([self.knowledge_values[xs] for xs in x])
        else:
            knowledge = self.knowledge_values[x]
        return 1.0 + knowledge