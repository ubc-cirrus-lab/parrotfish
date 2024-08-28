from abc import ABC
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from .config_manager import ConfigManager
from .cost_calculator import CostCalculator
from .invoker import Invoker
from ..exception import InvocationError
from ..logger import logger


class Explorer2D(ABC):
    """This class provides the operation of serverless function's exploration."""

    def __init__(
        self,
        config_manager: ConfigManager,
        invoker: Invoker,
        price_calculator: CostCalculator,
        cpu_mem_space: set,
        payload: str = None,
        cpu_bounds: list = None,
        memory_bounds: list = None,
    ):
        self.config_manager = config_manager
        self.invoker = invoker
        self.price_calculator = price_calculator
        self.payload = payload

        list_cpu_mem_tuple = list(cpu_mem_space)
        list_cpu_mem_tuple.sort(key=lambda x: (x[0], x[1]))
        list_cpu_mem = [[c, m] for c, m in list_cpu_mem_tuple]
        self.cpu_mem_space = np.array(list_cpu_mem)

        if cpu_bounds or memory_bounds:
            self.cpu_mem_space = self.cpu_mem_space[
                (self.cpu_mem_space[:, 0] >= cpu_bounds[0] if cpu_bounds is not None else True) &
                (self.cpu_mem_space[:, 0] <= cpu_bounds[1] if cpu_bounds is not None else True) &
                (self.cpu_mem_space[:, 1] >= memory_bounds[0] if memory_bounds is not None else True) &
                (self.cpu_mem_space[:, 1] <= memory_bounds[1] if memory_bounds is not None else True) 
            ]

        self.cost = 0
        self._cpu_config = 0.0
        self._memory_config_mb = 0

    def explore_parallel(
        self, nbr_invocations: int, nbr_threads: int, cpu: float = None, memory_mb: int = None
    ) -> list:
        """Invokes the specified serverless function multiple times with a given memory config and payload.

        Args:
            nbr_invocations (int): The number of invocations to performed with a given memory configuration.
            nbr_threads (int): The number of threads to invoke the serverless function.
            memory_mb (int): The target configuration's memory size in MB.

        Returns:
            list: List of all the invocations' durations.

        Raises:
             ExplorationError: If an error occurred while exploring with the memory config @memory_mb.

        If the memory_mb input is provided, it updates the memory configuration for the serverless function if it doesn't match.
        """
        # Check and set memory configuration
        if memory_mb or cpu:
            self.config_manager.set_config(memory_mb=memory_mb, cpu = cpu)
            if memory_mb is not None: self._memory_config_mb = memory_mb
            if cpu is not None: self._cpu_config = cpu
            # Handling cold start
            self.explore_parallel(nbr_invocations, nbr_threads)

        # Concurrent exploration.
        error = None
        results = []
        with ThreadPoolExecutor(max_workers=nbr_threads) as executor:
            # Submit exploration jobs to each thread.
            futures = [
                executor.submit(
                    self.explore, memory_mb=None, enable_cost_calculation=False
                )
                for _ in range(nbr_invocations)
            ]

            # Aggregate results from all threads.
            for future in as_completed(futures):
                try:
                    results.append(future.result())

                except InvocationError as e:
                    logger.debug(e)
                    if error is None:
                        error = e
                    continue

        # If one thread raises an invocation error we raise it.
        if error:
            raise error

        return results

    def explore(self, cpu: float = None, memory_mb: int = None, enable_cost_calculation=False) -> int:
        """Invokes the function and parses the execution response.

        Args:
            CPU (float, optional): CPU size in vCPU to configure the function for the exploration. Default to None.
            memory_mb (int, optional): Memory size in MB to configure the function for the exploration. Default to None.
            enable_cost_calculation (bool, optional): Specifies whether to compute the cost of the exploration. Default to False.

        Returns:
            int: The execution time of the serverless function in ms.

        Raises:
            ExplorationError: If an error occurred while exploring with the cpu config @cpu and memory config @memory_mb.

        If the cpu or memory_mb input is provided, it updates the cpu or memory configuration for the serverless function if it doesn't match.
        If the is_compute_cost input is provided, it computes the exploration cost and adds that to the total cost.
        """
        if memory_mb or cpu:
            self.config_manager.set_config(memory_mb=memory_mb, cpu = cpu)
            if memory_mb is not None: self._memory_config_mb = memory_mb
            if cpu is not None: self._cpu_config = cpu
            # Handling cold start
            self.explore(enable_cost_calculation=enable_cost_calculation)

        try:
            exec_time = self.invoker.invoke(self.payload)

        except InvocationError as e:
            logger.debug(e)
            if enable_cost_calculation:
                self.cost += self.price_calculator.calculate_price(
                    self._memory_config_mb, e.duration_ms, self._cpu_config
                )
            raise

        else:
            if enable_cost_calculation:
                self.cost += self.price_calculator.calculate_price(
                    self._memory_config_mb, exec_time, self._cpu_config
                )
            return exec_time
