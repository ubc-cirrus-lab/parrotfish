import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from .cost_calculator import CostCalculator
from .log_parser import LogParser
from src.exceptions import *


class Explorer(ABC):
    """This class provides the operation of serverless function's exploration."""

    def __init__(
        self,
        function_name: str,
        payload: str,
        log_parser: LogParser,
        price_calculator: CostCalculator,
    ):
        self.function_name = function_name
        self.payload = payload
        self.log_parser = log_parser
        self.price_calculator = price_calculator

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
        if memory_mb is not None:
            self.check_and_set_memory_config(memory_mb)
            self._memory_config_mb = memory_mb

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
        if error is not None:
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
        if memory_mb is not None:
            self.check_and_set_memory_config(memory_mb)
            self._memory_config_mb = memory_mb

        try:
            response = self.invoke()
            exec_time = self.log_parser.parse_log(response)

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

    @abstractmethod
    def check_and_set_memory_config(self, memory_mb: int) -> any:
        """Checks if the configured memory value is equal to @memory_mb and if no match it updates the serverless
        function's configuration by setting the memory value to @memory_mb.

        Args:
            memory_mb (int): The memory size in MB.

        Returns:
            any: The retrieved configuration of the serverless function.

        Raises:
            MemoryConfigError: If checking or updating the function's memory configuration fails.
        """
        pass

    @abstractmethod
    def invoke(self) -> str:
        """Invokes the serverless function with the payload @payload and returns the response.

        Returns:
            str: The logs returned by the function in response to the invocation.

        Raises:
            InvocationError: If the invocation cannot be performed. (Possibly function not found, user not authorised,
            or payload is wrong ...), or if the maximum number of exploration's attempts is reached.
        """
        pass
