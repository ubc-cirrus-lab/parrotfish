from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from src.exception import UnfeasibleConstraintError
from src.logging import logger
from src.sampling import Sample


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
    params: any = None

    def __call__(self, x: int or np.ndarray):
        return self.function(x, *self.params)

    def fit(self, sample: Sample) -> None:
        """Use non-linear least squares to fit a function to the sample.
        Optimize the parameters values so that the sum of the squared residuals is minimized.

        Args:
            sample (Sample): The sample to fit the function to.

        Raises:
            RuntimeError: if least-squares minimization fails.
        """
        if self.params is None:
            self.params = [sample.durations[0] // 10] * 3

        self.params = curve_fit(
            f=self.function,
            xdata=sample.memories,
            ydata=sample.costs,
            maxfev=int(1e8),
            p0=self.params,
            bounds=self.bounds,
        )[0]

    def minimize(
        self, memory_space: np.ndarray, execution_time_threshold: int = None
    ) -> int:
        """Minimizes the cost function and returns the corresponding memory configuration.

        Args:
            memory_space (np.ndarray): The memory space specific to the cloud provider.
            execution_time_threshold (int): The execution time threshold constraint.

        Returns:
            int: Memory configuration that minimizes the cost function.
        """
        costs = self.__call__(memory_space)

        # Handling execution threshold constraint
        if execution_time_threshold:
            try:
                memory_space, costs = self._filter_execution_time_constraint(
                    memory_space, costs, execution_time_threshold
                )
            except UnfeasibleConstraintError as e:
                logger.warning(e)

        min_index = np.argmin(costs)
        return memory_space[min_index]

    def _filter_execution_time_constraint(
        self,
        memory_space: np.ndarray,
        costs: np.ndarray,
        execution_time_threshold: int = None,
    ) -> tuple:
        filtered_memories = np.array([])
        filtered_costs = np.array([])
        execution_times = costs / memory_space

        for i in range(len(execution_times)):
            if execution_times[i] <= execution_time_threshold:
                filtered_memories = np.append(filtered_memories, memory_space[i])
                filtered_costs = np.append(filtered_costs, costs[i])

        if len(filtered_memories) == 0:
            raise UnfeasibleConstraintError(
                "The execution time threshold constraint cannot be satisfied"
            )

        return filtered_memories, filtered_costs
