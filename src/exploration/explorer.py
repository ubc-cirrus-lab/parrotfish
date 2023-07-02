import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from .cost_calculator import CostCalculator
from .log_parser import LogParser
from src.exceptions import *


class Explorer(ABC):
    """This is an abstract class to invoke serverless functions.

    This class provides the operation of serverless function's exploration.
    """

    def __init__(self, function_name: str, payload: str, log_parser: LogParser, price_calculator: CostCalculator):
        self.function_name = function_name
        self.payload = payload
        self.log_parser = log_parser
        self.price_calculator = price_calculator

        self.cost = 0
        self._memory_config_mb = None

        self._logger = logging.getLogger(__name__)

    def explore_parallel(self, nbr_invocations: int, nbr_threads: int, memory_mb: int = None) -> list:
        """Invokes the specified serverless function multiple times with a given memory config and payload.
        If the memory configuration doesn't match it will redeploy the function with the @memory_mb value.

        Args:
            nbr_invocations (int): The number of invocations to performed with a given memory configuration.
            nbr_threads (int): The number of threads to invoke the serverless function.
            memory_mb (int): The target configuration's memory size in MB.

        Returns:
            list: List of all the invocations' durations.

        Raises:
             ExplorationError: If an error occurred while exploring with the memory config @memory_mb.
        """
        try:
            if memory_mb is not None:
                self.check_and_set_memory_config(memory_mb)
                self._memory_config_mb = memory_mb

            with ThreadPoolExecutor(max_workers=nbr_threads) as executor:
                # Submit exploration jobs to each thread.
                futures = [executor.submit(self.explore, memory_mb=None, is_compute_cost=False)
                           for _ in range(nbr_invocations)]

                # Aggregate results from all threads.
                results = [future.result() for future in as_completed(futures)]

                # Calculate the cost
                self.cost += np.sum(
                    self.price_calculator.calculate_price(self._memory_config_mb, np.array(results)))

        except ExplorationError as e:
            self._logger.error("Exploration error in Explorer.explore_parallel")
            self._logger.debug(e)
            raise

        else:
            return results

    def explore(self, memory_mb: int = None, is_compute_cost=True) -> int:
        """Invokes the function with the payload @payload and returns the response parsed.

        Args:
            memory_mb (int): The target configuration's memory size in MB.
            is_compute_cost (bool): If we want to compute the exploration and add it to exploration cost.

        Returns:
            int: Billed duration of the serverless function's exploration.

        Raises:
            ExplorationError: If an error occurred while exploring with the memory config @memory_mb.
        """
        try:
            if memory_mb is not None:
                self.check_and_set_memory_config(memory_mb)
                self._memory_config_mb = memory_mb

            response = self.invoke()
            exec_time = self.log_parser.parse_log(response)

            if is_compute_cost:
                self.cost += self.price_calculator.calculate_price(self._memory_config_mb, exec_time)

        except ExplorationError as e:
            self._logger.error("Exploration error in Explorer.explore")
            self._logger.debug(e)
            raise

        else:
            return exec_time

    @abstractmethod
    def check_and_set_memory_config(self, memory_mb: int) -> dict:
        """Abstract method for checking if the configured memory value is equal to @memory_mb and if no match it
         updates the serverless function's configuration by setting the memory value to @memory_mb.

        Args:
            memory_mb (int): The memory size in MB.

        Returns:
            dict: The retrieved configuration of the serverless function.

        Raises:
            MemoryConfigError: If checking or updating the function's memory configuration fails.
        """
        pass

    @abstractmethod
    def invoke(self) -> str:
        """Abstract method for invoking the serverless function with the payload @payload and returns the response.

        Returns:
            str: The logs returned by function in response to the exploration.

        Raises:
            InvocationError: If the exploration cannot be performed. (Possibly function not found, user not authorised,
            or payload is wrong ...), or if the maximum number of exploration's attempts is reached.
        """
        pass
