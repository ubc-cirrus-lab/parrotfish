import numpy as np
import scipy.stats as stats
from abc import ABC, abstractmethod

from spot.constants import ALPHA, NORMAL_SCALE
from spot.recommendation_engine.utility import Utility


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
        self.knowledge_values = {
            x: 0 for x in range(self.memory_range[0], self.memory_range[1] + 1)
        }
        self.ratio = 1

    def get_value(self, x):
        return self.knowledge_values[x] + ALPHA * self.normalized_cost(x)

    def update_knowledge(self, x):
        for key in self.knowledge_values:
            self.knowledge_values[key] += self.get_normal_value(key, x, NORMAL_SCALE)
        self.ratio *= 1 / sum(list(self.knowledge_values.values()))
        self.normalize()

    def get_normal_value(self, x, mean, std):
        return self.ratio * stats.norm.pdf(x, mean, std)

    def normalize(self):
        knowledge = self.knowledge_values
        sum = np.sum(list(knowledge.values()))
        for k in knowledge:
            knowledge[k] /= sum


class SkewedNormalObjective(NormalObjective):
    def __init__(self, sampler, memory_range):
        super().__init__(sampler, memory_range)

    def get_normal_value(self, x, mean, std):
        return (
            self.ratio
            * stats.skewnorm.pdf(x, (self.memory_range[1] - x) / 100, mean, std)
            / stats.skewnorm.pdf(mean, (self.memory_range[1] - x) / 100, mean, std)
        )


class DynamicNormalObjective(NormalObjective):
    def __init__(self, sampler, memory_range):
        super().__init__(sampler, memory_range)

    def get_normal_value(self, x, mean, std):
        return (
            self.ratio
            * stats.norm.pdf(x, mean, mean / 5)
            / stats.norm.pdf(mean, mean, mean / 5)
        )


class DynamicSTDNormalObjective1(NormalObjective):
    def __init__(self, sampler, memory_range):
        super().__init__(sampler, memory_range)

    def get_normal_value(self, x, mean, std):
        try:
            std = -1 / Utility.fnp(x, **self.sampler.function_parameters) + 20
        except KeyError:
            std = mean / 5
        return (
            self.ratio * stats.norm.pdf(x, mean, std) / stats.norm.pdf(mean, mean, std)
        )


class DynamicSTDNormalObjective2(NormalObjective):
    def __init__(self, sampler, memory_range):
        super().__init__(sampler, memory_range)

    def get_normal_value(self, x, mean, std):
        try:
            std = (
                1
                - Utility.fn(x, **self.sampler.function_parameters)
                / Utility.fn(self.memory_range[0], **self.sampler.function_parameters)
            ) * 300 + 20
        except KeyError:
            std = mean / 5
        return (
            self.ratio * stats.norm.pdf(x, mean, std) / stats.norm.pdf(mean, mean, std)
        )


class FitToRealCostObjective(Objective):
    def __init__(self, sampler, memory_range):
        super().__init__(sampler, memory_range)
        self.ratio = 1
        self.knowledge_values = {
            x: 0 for x in range(self.memory_range[0], self.memory_range[1] + 1)
        }

    def get_value(self, x):
        duration = Utility.fn(x, **self.sampler.function_parameters)
        real_cost = duration * x
        knowledge = self._get_normalized_knowledge(x)
        return real_cost * knowledge

    def update_knowledge(self, x):
        for key in self.knowledge_values:
            self.knowledge_values[key] += stats.norm.pdf(key, x, 20) / stats.norm.pdf(x, x, 20)

    def _get_normalized_knowledge(self, x):
        if isinstance(x, np.ndarray):
            knowledge = np.array([self.knowledge_values[xs] for xs in x])
        else:
            knowledge = self.knowledge[x]
        min_ = np.min(knowledge)
        max_ = np.max(knowledge)
        return 1. + 2. * (knowledge - min_) / (max_ - min_)
