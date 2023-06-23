from abc import ABC, abstractmethod
import pandas as pd
from botocore.exceptions import *
from concurrent.futures import ThreadPoolExecutor, as_completed

from .log_parser import LogParser
from ..exceptions import *


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
        """Invokes the specified serverless function multiple times with a given memory config and payload.
        If the memory configuration doesn't match it will redeploy the function with the @memory_mb value.

        Args:
            nbr_invocations (int): The number of invocations to performed with a given memory configuration.
            nbr_threads (int): The number of threads to invoke the serverless function.
            memory_mb (int): The target configuration's memory size in MB.
            payload (str): The payload to invoke the function with.

        Raises:
            FunctionMemoryConfigError: If checking or updating the serverless function's memory configuration fails.
            InvocationError: If serverless function's invocation fails.
            FunctionENOMEM: If serverless function's memory configuration is not enough for the function's execution.

        Returns:
            pd.DataFrame: A pandas DataFrame representing the parsed result log.
        """

        # Check if the configured memory value is equal to memory_mb, otherwise sets it.
        try:
            self.check_and_set_memory_value(memory_mb)
        except FunctionMemoryConfigError as e:
            print(e)  # TODO: Add logger and replace printing errors with logging level DEBUG.
            raise

        # Initializing invocation returned values.
        results = {key: [] for key in self.log_parser.log_parsing_keys}

        with ThreadPoolExecutor(max_workers=nbr_threads) as executor:
            # Submit invocation jobs to each thread.
            futures = [
                executor.submit(self._execute_and_parse_logs, payload=payload)
                for _ in range(nbr_invocations)
            ]

            # Aggregate results from all threads.
            for future in as_completed(futures):
                result = future.result()
                for key in result.keys():
                    results[key].append(result[key])

        return pd.DataFrame.from_dict(results)

    def _execute_and_parse_logs(self, payload: str) -> dict:
        """Invokes the function with the payload @payload and returns the response parsed.

        Args:
            payload (str): Payload to invoke the Lambda function with.

        Returns:
            dict: The invocation's result parsed.

        Raises:
            InvocationError: If an error occurred while invoking the lambda function or the function raises an exception.
            FunctionENOMEM: If the memory configuration is not sufficient for lambda execution.
        """
        # TODO: Add logger and replace printing errors with logging level DEBUG.
        response = self.execute_function(payload)

        try:
            return self.log_parser.parse_log(response)

        except FunctionTimeoutError as e:
            print(e)
            raise FunctionENOMEM

        except ReadTimeoutError:
            print("Lambda invocation timed out. The API request to the AWS Lambda service, took longer than "
                  "the specified timeout period. Retry ...")
            self._execute_and_parse_logs(payload)  # Retry again

    @abstractmethod
    def check_and_set_memory_value(self, memory_mb: int) -> dict:
        """Abstract method for checking if the configured memory value is equal to @memory_mb and if no match it
         updates the serverless function's configuration by setting the memory value to @memory_mb.

        Args:
            memory_mb (int): The memory size in MB.

        Returns:
            dict: The retrieved configuration of the serverless function.

        Raises:
            FunctionMemoryConfigError: If checking or updating the function's memory configuration fails.
        """
        pass

    @abstractmethod
    def execute_function(self, payload: str) -> str:
        """Abstract method for invoking the serverless function with the payload @payload and returns the response
        base64 decoded.

        Args:
            payload (str): Payload to invoke the function with.

        Returns:
            str: The logs returned by AWS Lambda in response to the invocation. Logs are base64 decoded.

        Raises:
            InvocationError: If the invocation cannot be performed. (Possibly function not found, user not authorised,
            or payload is wrong ...), or if the maximum number of invocation's attempts is reached.
        """
        pass
