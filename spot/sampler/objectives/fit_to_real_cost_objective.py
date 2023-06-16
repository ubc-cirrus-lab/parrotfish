import numpy as np
import scipy.stats as stats
from . import Objective
from spot.data_model import *


class FitToRealCostObjective(Objective):
    # This class performs better than the normal class so
    def __init__(self, fitting_function: FittingFunction, memory_range: list):
        super().__init__(fitting_function, memory_range)
        self.knowledge_values = {
            x: 0 for x in range(self.memory_range[0], self.memory_range[1] + 1)
        }

    def get_value(self, x):
        real_cost = self.fitting_function(x)
        knowledge = self.get_knowledge(x)
        return real_cost * knowledge

    def update_knowledge(self, x):
        # Here we divide the normal distro by the mean to have the area under the curve is 1.
        # We no longer need this to be called.
        for key in self.knowledge_values:
            self.knowledge_values[key] += stats.norm.pdf(key, x, 200) / stats.norm.pdf(x, x, 200)

    def get_knowledge(self, x):
        if isinstance(x, np.ndarray):
            knowledge = np.array([self.knowledge_values[xs] for xs in x])
        else:
            knowledge = self.knowledge_values[x]
        return 1.0 + knowledge # Here we add 1.0 because we don't want the memory values we didn't explore to be 0 that will make cost * knowledge 0, if 0 it's only the cost which matters, knowledge is like a penalty for the sample.
