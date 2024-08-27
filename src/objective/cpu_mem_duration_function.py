from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from src.exception import UnfeasibleConstraintError
from src.logging import logger
from src.sampling import Sample2D
from typing import Union

@dataclass
class CpuMemDurationFunction:
    """Class for keeping track of the parametric function.

    Attributes:
        function (callable): the function we want to fit to the sample.
        params (np.array): parameters of the function.
        bounds (tuple): Lower and upper bounds on parameters.
    """
    # 1 / (a + (np.minimum(CPU + c, f) * b) * (Memory)) + d
    function: callable = lambda cpu_mem, a0, a1, a2, a3, a4: 1/ (a0 + (np.minimum(cpu_mem[0] + a1, a2) * a3) * cpu_mem[1]) + a4
    bounds: tuple = ([-np.inf, -np.inf, -np.inf, -np.inf, -np.inf], [np.inf, np.inf, np.inf, np.inf, np.inf])
    params: any = None

    def __call__(self, cpu_mem: tuple[Union[int, np.ndarray]]):
        return self.function(cpu_mem, *self.params)

    def fit(self, sample: Sample2D) -> None:
        """Use non-linear least squares to fit a function to the sample.
        Optimize the parameters values so that the sum of the squared residuals is minimized.

        Args:
            sample (Sample): The sample to fit the function to.

        Raises:
            RuntimeError: if least-squares minimization fails.
        """
        if self.params is None:
            self.params = [0.01, -0.001, 1, 0.1, 0.1]

        self.params = curve_fit(
            f=self.function,
            xdata=(sample.cpu_mems[:,0], sample.cpu_mems[:,1]),
            ydata=sample.durations,
            maxfev=int(1e8),
            p0=self.params,
            bounds=self.bounds,
        )[0]

    def minimize(
            self, cpu_mem_space: np.ndarray, constraint_execution_time_threshold: int = None,
            constraint_cost_tolerance_percent: int = None
    ) -> list[float, int]:
        """Minimizes the cost function and returns the corresponding memory configuration.

        Args:
            cpu_mem_space (np.ndarray): The cpu-memory space specific to the cloud provider.
            constraint_execution_time_threshold (int): The execution time threshold constraint.
            constraint_cost_tolerance_percent (int): The cost tolerance window constraint.

        Returns:
            int: Memory configuration that minimizes the cost function.
        """
        costs = self.__call__((cpu_mem_space[:, 0], cpu_mem_space[:, 1])) * (cpu_mem_space[:, 0] * 0.00002400 + cpu_mem_space[:, 1] * 0.00000250 / 1024)

        # Handling execution threshold constraint
        if constraint_execution_time_threshold:
            try:
                cpu_mem_space, costs = self._filter_execution_time_constraint(
                    cpu_mem_space, costs, constraint_execution_time_threshold
                )
            except UnfeasibleConstraintError as e:
                logger.warning(e)

        if constraint_cost_tolerance_percent:
            execution_times = costs / (cpu_mem_space[:, 0] + cpu_mem_space[:, 1])
            min_index = self._find_min_index_within_tolerance(costs, execution_times, constraint_cost_tolerance_percent)
        else:
            min_index = np.argmin(costs)
        return cpu_mem_space[min_index]

    @staticmethod
    def _find_min_index_within_tolerance(costs: np.ndarray, execution_times: np.ndarray,
                                         constraint_cost_tolerance_percent: int) -> int:
        min_cost = np.min(costs)
        min_cost_tolerance_window = min_cost + constraint_cost_tolerance_percent / 100 * min_cost
        min_index = 0
        min_execution_time = np.inf
        for i in range(len(execution_times)):
            if costs[i] <= min_cost_tolerance_window:
                if execution_times[i] < min_execution_time:
                    min_index = i
                    min_execution_time = execution_times[i]
        return min_index

    @staticmethod
    def _filter_execution_time_constraint(
            cpu_mem_space: np.ndarray,
            costs: np.ndarray,
            constraint_execution_time_threshold: int = None,
    ) -> tuple:
        filtered_cpu_mems = np.array([])
        filtered_costs = np.array([])
        execution_times = costs / (cpu_mem_space[:, 0] + cpu_mem_space[:, 1])

        for i in range(len(execution_times)):
            if execution_times[i] <= constraint_execution_time_threshold:
                filtered_cpu_mems = np.append(filtered_cpu_mems, cpu_mem_space[i])
                filtered_costs = np.append(filtered_costs, costs[i])

        if len(filtered_cpu_mems) == 0:
            raise UnfeasibleConstraintError()

        return filtered_cpu_mems, filtered_costs
