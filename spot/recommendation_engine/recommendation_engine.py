import numpy as np
import pandas as pd

from spot.recommendation_engine.objectives import *
from spot.recommendation_engine.utility import Utility
from spot.constants import *
from spot.invocation.aws_lambda_invoker import LambdaENOMEM


class DataPoint:
    def __init__(self, memory, billed_time):
        self.memory = memory
        self.billed_time = billed_time


class RecommendationEngine:
    def __init__(self, invocator, payload_path, memory_range):
        self.payload_path = payload_path
        self.function_invocator = invocator
        self.sampled_datapoints = []
        self.fitted_function = None
        self.function_parameters = {}
        self.memory_range = memory_range
        if OPTIMIZATION_OBJECTIVE == "normal":
            self.objective = NormalObjective(self, self.memory_range)
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
        while (
            self.sampled_memories_count < TOTAL_SAMPLE_COUNT
            and self._termination_value() < TERMINATION_THRESHOLD
        ):
            x = self._choose_sample_point()
            self.sample(x)
            self.fitted_function, self.function_parameters = Utility.fit_function(
                self.sampled_datapoints
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
        def update_sample_memories(mems):
            mems[0] += 128
            mems[1] = (mems[0] * 2 + mems[2]) // 3

        sample_memories = INITIAL_SAMPLE_MEMORIES
        while True:
            enomem = False
            for x in sample_memories:
                try:
                    self.sample(x)
                except LambdaENOMEM:
                    enomem = True
                    break
            if not enomem:
                break
            update_sample_memories(sample_memories)
            print('ENOMEM: trying with new memories', sample_memories)

        self.fitted_function, self.function_parameters = Utility.fit_function(
            self.sampled_datapoints
        )

    def sample(self, x):
        def _closest_termination_cv_and_values(values):
            _min = 1000
            _min_val = None
            for i in range(len(values) - 1):
                cv = Utility.cv(values[i : i + 2])
                if _min > cv:
                    _min = cv
                    _min_val = values[i : i + 2]
            return _min, _min_val

        print(f"Sampling {x}")
        # Cold start
        if HANDLE_COLD_START:
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
                and _closest_termination_cv_and_values(values)[0] > TERMINATION_CV
            ):
                result = self.function_invocator.invoke(
                    invocation_count=1,
                    parallelism=1,
                    memory_mb=x,
                    payload_filename=self.payload_path,
                )
                values.append(result.iloc[0]["Billed Duration"])

        values.sort()
        if len(values) > DYNAMIC_SAMPLING_INITIAL_STEP:
            selected_values = _closest_termination_cv_and_values(values)[1]
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
        return [x for x in memories if x not in sampled_memories]

    def _termination_value(self):
        mems = np.arange(self.memory_range[0], self.memory_range[1] + 1)
        knowledge = self.objective.get_knowledge(mems)
        y = self.fitted_function(mems, *self.function_parameters)
        idx = np.argmin(y)
        return knowledge[idx]
