import logging
from abc import ABC
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from .config_manager import ConfigManager
from .cost_calculator import CostCalculator
from .invoker import Invoker
from .log_parser import LogParser
from ..exceptions import InvocationError


class Explorer(ABC):
    """This class provides the operation of serverless function's exploration."""

    def __init__(
        self,
        config_manager: ConfigManager,
        invoker: Invoker,
        log_parser: LogParser,
        price_calculator: CostCalculator,
        memory_space: set,
        memory_bounds: list = None,
    ):
        self.config_manager = config_manager
        self.invoker = invoker
        self.log_parser = log_parser
        self.price_calculator = price_calculator

        self.memory_space = np.array(list(memory_space), dtype=int)
        if memory_bounds:
            self.memory_space = np.array(
                list(
                    memory_space.intersection(
                        range(memory_bounds[0], memory_bounds[1] + 1)
                    )
                ), dtype=int
            )

        self.cost = 0
        self._memory_config_mb = 0

        self._logger = logging.getLogger(__name__)

    def explore_parallel(
        self, nbr_invocations: int, nbr_threads: int, memory_mb: int = None
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
        if memory_mb:
            self.config_manager.set_config(memory_mb)
            self._memory_config_mb = memory_mb
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
                    self._logger.debug(e)
                    if error is None:
                        error = e
                    self.cost += self.price_calculator.calculate_price(
                        self._memory_config_mb, e.duration_ms
                    )
                    continue

        # If one thread raises an invocation error we raise it.
        if error:
            raise error

        # Calculate the cost
        self.cost += np.sum(
            self.price_calculator.calculate_price(
                self._memory_config_mb, np.array(results)
            )
        )

        return results

    def explore(self, memory_mb: int = None, enable_cost_calculation=True) -> int:
        """Invokes the function and parses the execution response.

        Args:
            memory_mb (int, optional): Memory size in MB to configure the function for the exploration. Default to None.
            enable_cost_calculation (bool, optional): Specifies whether to compute the cost of the exploration. Default to True.

        Returns:
            int: The execution time of the serverless function in ms.

        Raises:
            ExplorationError: If an error occurred while exploring with the memory config @memory_mb.

        If the memory_mb input is provided, it updates the memory configuration for the serverless function if it doesn't match.
        If the is_compute_cost input is provided, it computes the exploration cost and adds that to the total cost.
        """
        if memory_mb:
            self.config_manager.set_config(memory_mb)
            self._memory_config_mb = memory_mb
            # Handling cold start
            self.explore(enable_cost_calculation=enable_cost_calculation)

        try:
            execution_log = self.invoker.invoke()
            exec_time = self.log_parser.parse_log(execution_log)

        except InvocationError as e:
            self._logger.debug(e)
            if enable_cost_calculation:
                self.cost += self.price_calculator.calculate_price(
                    self._memory_config_mb, e.duration_ms
                )
            raise

        else:
            if enable_cost_calculation:
                self.cost += self.price_calculator.calculate_price(
                    self._memory_config_mb, exec_time
                )
            return exec_time
