import os

import numpy as np
import pandas as pd

from spot.recommendation_engine.objectives import *
from spot.recommendation_engine.utility import Utility

from spot.constants import *


class DataPoint:
    def __init__(self, memory, billed_time):
        self.memory = memory
        self.billed_time = billed_time


class RecommendationEngine:
    def __init__(self, invocator, payload_path, memory_range):
        self.payload_path = payload_path
        self.function_invocator = invocator
        self.sampled_datapoints = []
        self.sampled_point_count = 0
        self.fitted_function = None
        self.function_parameters = {}
        self.function_degree = 2
        self.memory_range = memory_range
        if OPTIMIZATION_OBJECTIVE == "normal":
            self.objective = NormalObjective(self, self.memory_range)
        elif OPTIMIZATION_OBJECTIVE == "skewnormal":
            self.objective = SkewedNormalObjective(self, self.memory_range)
        elif OPTIMIZATION_OBJECTIVE == "dynamicnormal":
            self.objective = DynamicNormalObjective(self, self.memory_range)
        elif OPTIMIZATION_OBJECTIVE == "dynamic_std1":
            self.objective = DynamicSTDNormalObjective1(self, self.memory_range)
        elif OPTIMIZATION_OBJECTIVE == "dynamic_std2":
            self.objective = DynamicSTDNormalObjective2(self, self.memory_range)
        elif OPTIMIZATION_OBJECTIVE == "fit_to_real_cost":
            assert len(INITIAL_SAMPLE_MEMORIES) == 3
            self.objective = FitToRealCostObjective(self, self.memory_range)

        self.exploration_cost = 0

    def get_function(self):
        return self.fitted_function, self.function_parameters

    @property
    def sampled_memories_count(self):
        return len(set([x.memory for x in self.sampled_datapoints]))

    def run(self):
        self.initial_sample()
        self.sampled_point_count = 2
        while (
            self.sampled_memories_count < TOTAL_SAMPLE_COUNT
            and self.objective.ratio > KNOWLEDGE_RATIO
        ):
            x = self._choose_sample_point()
            self.sample(x)
            self.sampled_point_count += 1
            self.function_degree = min(self.sampled_point_count, 4)
            self.fitted_function, self.function_parameters = Utility.fit_function(
                self.sampled_datapoints, degree=self.function_degree
            )

            while (
                Utility.check_function_validity(
                    self.fitted_function, self.function_parameters, self.memory_range
                )
                is False
            ):
                self.function_degree -= 1
                self.fitted_function, self.function_parameters = Utility.fit_function(
                    self.sampled_datapoints, degree=self.function_degree
                )
        return self.report()

    def report(self):
        minimum_memory, minimum_cost = Utility.find_minimum_memory_cost(
            self.fitted_function, self.function_parameters, self.memory_range
        )
        result = {
            "Minimum Cost Memory": [minimum_memory],
            "Expected Cost": [minimum_cost],
            "Exploration Cost": [self.exploration_cost],
        }
        return pd.DataFrame.from_dict(result)

    def initial_sample(self):
        # TODO: ensure initial memories are in the accepted memory range.
        for x in INITIAL_SAMPLE_MEMORIES:
            self.sample(x)

        self.fitted_function, self.function_parameters = Utility.fit_function(
            self.sampled_datapoints, degree=self.function_degree
        )

    def sample(self, x):
        print(f"Sampling {x}")
        # Cold start
        result = self.function_invocator.invoke(
            invocation_count=DYNAMIC_SAMPLING_INITIAL_STEP,
            parallelism=DYNAMIC_SAMPLING_INITIAL_STEP,
            memory_mb=x,
            payload_filename=self.payload_path,
            save_to_ctx=False,
        )
        durations = result["Billed Duration"].to_numpy()
        self.exploration_cost += np.sum(Utility.calculate_cost(durations, x))
        result = self.function_invocator.invoke(
            invocation_count=DYNAMIC_SAMPLING_INITIAL_STEP,
            parallelism=DYNAMIC_SAMPLING_INITIAL_STEP,
            memory_mb=x,
            payload_filename=self.payload_path,
        )
        values = result["Billed Duration"].tolist()
        if IS_DYNAMIC_SAMPLING_ENABLED:
            while (
                len(values) < DYNAMIC_SAMPLING_MAX
                and Utility.cv(values) > TERMINATION_CV
            ):
                result = self.function_invocator.invoke(
                    invocation_count=1,
                    parallelism=1,
                    memory_mb=x,
                    payload_filename=self.payload_path,
                )
                values.append(result.iloc[0]["Billed Duration"])

        if len(values) > 2:
            values.sort()
            selected_values = values[len(values) // 2 - 1 : len(values) // 2]
        else:
            selected_values = values

        self.exploration_cost += np.sum(Utility.calculate_cost(np.array(values), x))

        for value in selected_values:
            self.sampled_datapoints.append(DataPoint(memory=x, billed_time=value))

        print(f"finished sampling {x} with {len(values)} samples")
        self.objective.update_knowledge(x)

    def invoke_once(self, memory_mb, is_warm=True):
        if not is_warm:
            # Cold start
            self.function_invocator.invoke(
                invocation_count=1,
                parallelism=1,
                memory_mb=memory_mb,
                payload_filename=self.payload_path,
                save_to_ctx=False,
            )
        result = self.function_invocator.invoke(
            invocation_count=1,
            parallelism=1,
            memory_mb=memory_mb,
            payload_filename=self.payload_path,
        )
        return result

    def _choose_sample_point(self):
        mems = np.array(self._remainder_memories(), dtype=np.double)
        values = self.objective.get_value(mems)
        index = np.argmin(values)
        return int(mems[index])

    def _remainder_memories(self):
        memories = range(self.memory_range[0], self.memory_range[1] + 1)
        sampled_memories = set(
            [datapoint.memory for datapoint in self.sampled_datapoints]
        )
        remainder = [x for x in memories if x not in sampled_memories]
        return remainder
