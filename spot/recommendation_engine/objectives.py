import numpy as np
import scipy.stats as stats
from abc import ABC, abstractmethod

ALPHA = 0.001
NORMAL_SCALE = 100


class Objective(ABC):
    def __init__(self, sampler, memory_range):
        self.sampler = sampler
        self.memory_range = memory_range

    def normalized_cost(self, x):
        return (
            self.sampler.fitted_function(x, **self.sampler.function_parameters)
            * x
            / self._min_cost()
        )

    def _min_cost(self):
        min_cost = np.inf
        for memory_value in range(self.memory_range[0], self.memory_range[1] + 1):
            cost = (
                self.sampler.fitted_function(
                    memory_value, **self.sampler.function_parameters
                )
                * memory_value
            )
            if cost < min_cost:
                min_cost = cost
        return min_cost

    @abstractmethod
    def get_value(self, x):
        pass

    @abstractmethod
    def update_knowledge(self, x):
        pass


class NormalObjective(Objective):
    def __init__(self, sampler, memory_range):
        super().__init__(sampler, memory_range)
        self.knowledge_values = {}
        for x in range(self.memory_range[0], self.memory_range[1] + 1):
            self.knowledge_values[x] = 0
        self.ratio = 1

    def get_value(self, x):
        return self.knowledge_values[x] + ALPHA * self.normalized_cost(x)

    def update_knowledge(self, x):
        for key, _ in self.knowledge_values.items():
            self.knowledge_values[key] += NormalObjective.get_normal_value(
                key, x.memory, NORMAL_SCALE, self.ratio
            )
        self.ratio *= 1 / sum(list(self.knowledge_values.values()))
        self.normalize()

    @staticmethod
    def get_normal_value(x, mean, std, ratio):
        return ratio * stats.norm.pdf(x, mean, std)

    def normalize(self):
        knowledge = self.knowledge_values
        sum = np.sum(list(knowledge.values()))
        for k, v in knowledge.items():
            knowledge[k] = v / sum
