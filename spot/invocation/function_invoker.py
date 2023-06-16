from abc import ABC, abstractmethod
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..exceptions import *
from spot.invocation.logs_parsing import *


class FunctionInvoker(ABC):
    """This is an abstract class to invoke serverless functions.

    This class provides the operation of serverless function's invocation.
    This class is to be implemented for every cloud provider.
    """

    def __init__(self, function_name: str, log_parser: LogParser):
        self.function_name = function_name
        self.log_parser = log_parser

    def invoke(
        self,
        nbr_invocations: int,
        nbr_threads: int,
        memory_mb: int,
        payload: str,
    ) -> pd.DataFrame:
        """Invokes the specified serverless function multiple times with a given memory config and payload and returning
        a pandas DataFrame representing the execution logs_parsing.

        Args:
            nbr_invocations: The number of invocations with a given memory configuration.
            nbr_threads: The number of threads to invoke the serverless function.
            memory_mb: The memory size in MB.
            payload: The payload to invoke the function with.

        Raises:
            LambdaENOMEM: If not enough memory is configured.
            LambdaMemoryConfigError: If configuring the lambda function fails.
            LambdaInvocationError: If an error is occurred while invoking the lambda function.

        Returns:
            pd.DataFrame: A pandas DataFrame representing the parsed execution logs_parsing.
        """

        # Check if the actual memory value is equal to memory_mb, otherwise sets it.
        self.check_and_set_memory_value(memory_mb)
        is_memory_config_ok = False

        while True:
            # Initializing invocation returned values.
            results = {key: [] for key in self.log_parser.log_parsing_keys}
            errors = []

            with ThreadPoolExecutor(max_workers=nbr_threads) as executor:
                # Submit invocation jobs to each thread.
                futures = [
                    executor.submit(self.execute_and_parse_logs, payload=payload)
                    for _ in range(nbr_invocations)
                ]

                # Aggregate results from all threads.
                for future in as_completed(futures):
                    res, errors = future.result()
                    for key in self.log_parser.log_parsing_keys:
                        results[key].extend(res[key])

            if all([m == memory_mb for m in results["Memory Size"]]):
                is_memory_config_ok = True
                break

        if not is_memory_config_ok:
            raise LambdaMemoryConfigError

        if len(errors) != 0:
            raise LambdaInvocationError(errors)

        return pd.DataFrame.from_dict(results)

    @abstractmethod
    def check_and_set_memory_value(self, memory_mb: int) -> dict:
        """Abstract method for checking and setting the memory value.

        Args:
            memory_mb (int): The memory size in MB.

        Returns:
            dict: the retrieved configuration of the lambda function.
        """
        pass

    @abstractmethod
    def execute_and_parse_logs(self, payload: str) -> tuple:
        """Abstract method for sequentially invoking the serverless function.

        Args:
            payload (str): The payload to invoke the function with.

        Returns:
            tuple: A tuple containing the invocation results (str), and a list of errors (list).

        Raises:
            LambdaENOMEM: If the memory configuration is not sufficient for lambda execution.
        """
        pass
