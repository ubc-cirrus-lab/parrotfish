import spot.constants as const
import numpy as np
from ..exceptions import *
from ..invocation import *
from ..pricing import *
from ..data_model import *
from .objectives import Objective


class Sampler:
    def __init__(
            self,
            memory_range: list,
            payload: str,
            invoker: FunctionInvoker,
            objective: Objective,
            price_calculator: InvocationPriceCalculator,
            fitting_function: FittingFunction
    ):
        self.memory_range = memory_range
        self.payload = payload
        self.invoker = invoker
        self.objective = objective
        self.price_calculator = price_calculator
        self.fitting_function = fitting_function

        self.sampled_datapoints = []
        self.exploration_cost = 0
        self.initial_sample_memories = const.INITIAL_SAMPLE_MEMORIES

    @property
    def sampled_memories_count(self):
        return len(set([x.memory for x in self.sampled_datapoints]))

    @property
    def _remainder_memories(self):
        memories = range(self.memory_range[0], self.memory_range[1] + 1)
        sampled_memories = set(
            [datapoint.memory for datapoint in self.sampled_datapoints]
        )
        return [x for x in memories if x not in sampled_memories]

    @property
    def termination_value(self):
        # We have knowledge values and costs, we calculate the optimal point, and we finish once the knowledge on
        # the optimal point reaches a threshold
        memories = np.arange(self.memory_range[0], self.memory_range[1] + 1)
        knowledge = self.objective.get_knowledge(memories)
        y = self.fitting_function(memories)
        idx = np.argmin(y)
        return knowledge[idx]

    def initialize_sample(self):
        sample_memories = self.initial_sample_memories
        sample_memories[0] = max(sample_memories[0], self.memory_range[0])
        sample_memories[-1] = min(sample_memories[-1], self.memory_range[-1])
        sample_memories[1] = (sample_memories[0] * 2 + sample_memories[-1]) // 3

        for i in range(len(sample_memories)):
            while True:
                # mitigate the problem of too low memory config.
                try:
                    self.sample(sample_memories[i])
                except LambdaENOMEM:
                    sample_memories[0] += 128
                    sample_memories[1] = (sample_memories[0] * 2 + sample_memories[2]) // 3
                    print("ENOMEM: trying with new memories", sample_memories)
                else:
                    break

        self.memory_range[0] = sample_memories[0]
        self.memory_range[-1] = sample_memories[-1]

        self.fitting_function.fit(self.sampled_datapoints)

    def sample(self, memory_mb: int):
        print(f"Sampling {memory_mb}")
        # Cold start
        if const.HANDLE_COLD_START:
            # Because there are multiple instances to handle the invocation, cold start should be considered for each
            # invocation, that's why we invoke the function multiple times. DYNAMIC_SAMPLING_INITIAL_STEP is the number
            # of the initial invocation.
            result = self.invoker.invoke(
                nbr_invocations=const.DYNAMIC_SAMPLING_INITIAL_STEP,
                nbr_threads=const.DYNAMIC_SAMPLING_INITIAL_STEP,
                memory_mb=memory_mb,
                payload=self.payload,
            )
            durations = result["Billed Duration"].to_numpy()
            self.exploration_cost += np.sum(self.price_calculator.calculate_price(memory_mb, durations))

        # Do actual sampling, warm start.
        result = self.invoker.invoke(
            nbr_invocations=const.DYNAMIC_SAMPLING_INITIAL_STEP,
            nbr_threads=const.DYNAMIC_SAMPLING_INITIAL_STEP,
            memory_mb=memory_mb,
            payload=self.payload,
        )
        values = result["Billed Duration"].tolist()

        # Dynamic sampling means that we will invoke the function again and again until we have a fairly consistent
        # invocation values
        if const.IS_DYNAMIC_SAMPLING_ENABLED:
            while (
                    len(values) < const.DYNAMIC_SAMPLING_MAX
                    and self._closest_termination_cv_and_values(values)[0] > const.TERMINATION_CV
            ):
                result = self.invoker.invoke(
                    nbr_invocations=1,
                    nbr_threads=1,
                    memory_mb=memory_mb,
                    payload=self.payload,
                )
                values.append(result.iloc[0]["Billed Duration"])

        values.sort()  # Don't know

        if len(values) > const.DYNAMIC_SAMPLING_INITIAL_STEP:
            selected_values = self._closest_termination_cv_and_values(values)[1]
        else:
            selected_values = values

        self.exploration_cost += np.sum(self.price_calculator.calculate_price(memory_mb, np.array(values)))

        for value in selected_values:
            self.sampled_datapoints.append(DataPoint(memory=memory_mb, billed_time=value))

        print(f"finished sampling {memory_mb} with {len(values)} samples")
        self.objective.update_knowledge(memory_mb)

    def choose_sample_point(self):
        memories = np.array(self._remainder_memories, dtype=np.double)
        values = self.objective.get_value(memories)
        index = np.argmin(values)
        return int(memories[index])

    def _closest_termination_cv_and_values(self, values):
        def coefficient_variation(l):
            return np.std(l, ddof=1) / np.mean(l)
        # Calculates min cv (cv is calculates by pairs)
        _min = 1000
        _min_val = None
        for i in range(len(values) - 1):
            cv = coefficient_variation(values[i: i + 2])
            if _min > cv:
                _min = cv
                _min_val = values[i: i + 2]
        return _min, _min_val
