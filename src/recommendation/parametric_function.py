from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from src.data_model import Sample
from src.exceptions import NoMemoryLeftError


@dataclass
class ParametricFunction:
    """Class for keeping track of the parametric function.

    Attributes:
        function (callable): the function we want to fit to the sample.
        params (np.array): parameters of the function.
        bounds (tuple): Lower and upper bounds on parameters.
    """
    function: callable
    bounds: tuple
    params: np.array = None
    execution_time_threshold: float = None

    def __call__(self, x: np.array):
        return self.function(x, *self.params)

    def fit(self, sample: Sample) -> None:
        """Use non-linear least squares to fit a function to the datapoints.
        Optimize values for the parameters so that the sum of the squared residuals is minimized.

        Args:
            sample (Sample): The sample memories.

        Raises:
            RuntimeError: if least-squares minimization fails.
        """
        if self.params is None:
            # self.params = [sample.durations[0] // 10] * 3
            self.params = [1000, 10000, 100]
        self.params = curve_fit(
            f=self.function,
            xdata=sample.memories,
            ydata=sample.costs,
            maxfev=int(1e8),
            p0=self.params,
            bounds=self.bounds,
        )[0]

    def minimize(self, memory_space: np.ndarray) -> tuple:
        """Minimizes the cost function and returns the corresponding memory configuration.

        Returns:
            tuples: Memory configuration that minimizes the cost function and the corresponding cost value.

        Raises:
            NoMemoryLeftError: If no memory configuration meets the constraint on the execution time threshold.
        """
        costs = self.__call__(memory_space)

        # Handling execution threshold
        if self.execution_time_threshold is not None:
            filtered_memories = np.array([])
            filtered_costs = np.array([])
            execution_times = costs / memory_space
            for i in range(len(execution_times)):
                if execution_times[i] <= self.execution_time_threshold:
                    filtered_memories = np.append(filtered_memories, memory_space[i])
                    filtered_costs = np.append(filtered_costs, costs[i])
            memories = filtered_memories
            costs = filtered_costs
            if len(memories) == 0:
                raise NoMemoryLeftError()

        min_index = np.argmin(costs)
        return memory_space[min_index], costs[min_index]
