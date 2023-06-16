import sys
import pandas as pd
from spot.exceptions import *
from ..invocation import FunctionInvoker
from spot.sampler import *
from spot.constants import *
from spot.data_model import *
import numpy as np


class RecommendationEngine:
    def __init__(
        self,
        invoker: FunctionInvoker,
        memory_range: list,
        sampler: Sampler,
        fitting_function: FittingFunction,
        execution_time_threshold: float = None,
    ):
        self.function_invoker = invoker
        self.memory_range = memory_range
        self.fitting_function = fitting_function
        self.execution_time_threshold = execution_time_threshold
        self.sampler = sampler

    def run(self):
        self.sampler.initialize_sample()
        while (
            self.sampler.sampled_memories_count < TOTAL_SAMPLE_COUNT
            and self.sampler.termination_value < TERMINATION_THRESHOLD
        ):
            x = self.sampler.choose_sample_point()
            self.sampler.sample(x)
            self.fitting_function.fit_function(self.sampler.sampled_datapoints)
        return self.report()

    def report(self):
        try:
            minimum_memory, minimum_cost = self._find_minimum_memory_cost(
                self.memory_range,
                self.execution_time_threshold,
            )
            result = {
                "Minimum Cost Memory": [minimum_memory],
                "Expected Cost": [minimum_cost],
                "Exploration Cost": [self.sampler.exploration_cost],
            }
            return pd.DataFrame.from_dict(result)

        except NoMemoryLeftError:
            print(
                "No memory configuration is possible. The execution time threshold is too low!",
                file=sys.stderr,
            )
            exit(1)

    def invoke_once(self, memory_mb: int, payload: str, is_warm=True):
        if not is_warm:
            # Cold start
            self.function_invoker.invoke(
                nbr_invocations=1,
                nbr_threads=1,
                memory_mb=memory_mb,
                payload=payload,
            )
        return self.function_invoker.invoke(
            nbr_invocations=1,
            nbr_threads=1,
            memory_mb=memory_mb,
            payload=payload,
        )

    def _find_minimum_memory_cost(self, memory_range, execution_time_threshold: float = None):
        memories = np.arange(memory_range[0], memory_range[1] + 1, dtype=np.double)
        costs = self.fitting_function(memories)

        # Handling execution threshold
        if execution_time_threshold is not None:
            filtered_memories = np.array([])
            filtered_costs = np.array([])
            execution_times = costs / memories
            for i in range(len(execution_times)):
                if execution_times[i] <= execution_time_threshold:
                    filtered_memories = np.append(filtered_memories, memories[i])
                    filtered_costs = np.append(filtered_costs, costs[i])
            memories = filtered_memories
            costs = filtered_costs
            if len(memories) == 0:
                raise NoMemoryLeftError()

        min_index = np.argmin(costs)
        return memories[min_index], costs[min_index]
