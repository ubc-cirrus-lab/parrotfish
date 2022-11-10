import numpy as np
import random

from spot.recommendation_engine.objectives import NormalObjective
from spot.recommendation_engine.utility import Utility

SAMPLE_POINTS = [128, 2048]
MEMORY_RANGE = [128, 3008]
IS_DYNAMIC_SAMPLING_ENABLED = True
TOTAL_SAMPLE_COUNT = 20
RANDOM_SAMPLING = True
RANDOM_SEED = 0

IS_MULTI_FUNCTION = True

random.seed(RANDOM_SEED)


class RecommendationEngine:
    def __init__(self, invocator):
        self.function_invocator = invocator
        self.sampled_datapoints = []
        self.sampled_points = 0
        self.fitted_function = None
        self.function_parameters = {}
        self.function_degree = 2
        self.objective = NormalObjective(self, MEMORY_RANGE)

    def get_function(self):
        return self.fitted_function, self.function_parameters

    def run(self):
        self.initial_sample()
        self.sampled_points = 2
        while len(self.sampled_datapoints) < TOTAL_SAMPLE_COUNT and self.objective.ratio > 0.2:
            x = self.choose_sample_point()
            self.sample(x)
            self.sampled_points += 1
            self.function_degree = self.sampled_points
            self.fitted_function, self.function_parameters = Utility.fit_function(self.sampled_datapoints,
                                                                                  degree=self.function_degree)

            while Utility.check_function_validity(self.fitted_function, self.function_parameters,
                                                  MEMORY_RANGE) is False:
                self.function_degree -= 1
                self.fitted_function, self.function_parameters = Utility.fit_function(self.sampled_datapoints,
                                                                                      degree=self.function_degree)
        minimum_memory, minimum_cost = Utility.find_minimum_memory_cost(self.fitted_function, self.function_parameters,
                                                                        MEMORY_RANGE)
        print(f"{minimum_memory=}, with {minimum_cost=}")

    def initial_sample(self):
        for x in SAMPLE_POINTS:
            self.sample(x)
        self.fitted_function, self.function_parameters = Utility.fit_function(self.sampled_datapoints,
                                                                              degree=self.function_degree)

    def sample(self, x):
        # TODO: handle cold start
        # result = self.function_invocator.invoke(memory=x, is_parallel=True, count=2)
        # TODO: get result from invocation
        # result = self.function_invocator.invoke(memory=x, is_parallel=True, count=2)
        values = []
        if IS_DYNAMIC_SAMPLING_ENABLED:
            while len(values) < 5 and Utility.cv(values) > 0.3:
                # result = self.function_invocator.invoke(memory=x, count=1)
                # values.append(result['Billed time'])
                pass
        return values

    def choose_sample_point(self):
        max_value = MEMORY_RANGE[0]
        max_obj = np.inf
        for value in self.remainder_memories():
            obj = self.objective.get_value(value)
            if obj < max_obj:
                max_value = value
                max_obj = obj
        return max_value

    def remainder_memories(self):
        memories = range(MEMORY_RANGE[0], MEMORY_RANGE[1] + 1)
        sampled_memories = set([datapoint.memory for datapoint in self.sampled_datapoints])
        remainder = [x for x in memories if x not in sampled_memories]
        return remainder
