from abc import ABC, abstractmethod
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import botocore.exceptions
from ..exceptions import *
from ..context import Context


class FunctionInvoker(ABC):
    """This is an abstract class to invoke serverless functions.

    This class provides an interface to invoke a given serverless function.
    This class is to be implemented for every cloud provider.
    """

    def __init__(self, function_name: str, log_keys: list, client, context: Context):
        self.function_name = function_name
        self.log_keys = log_keys
        self.client = client
        self.context = context

    def invoke(
        self,
        invocation_count: int,
        nbr_threads: int,
        memory_mb: float,
        payload_file_path: str,
        save_to_ctx: bool = True,
    ) -> pd.DataFrame:
        """Invokes the specified serverless function multiple times with a given memory config and payload and returning
        a pandas DataFrame representing the execution logs.

        Args:
            invocation_count: The number of invocations for a given memory value.
            nbr_threads: The number of threads to invoke the serverless function.
            memory_mb: The size of the memory in MB.
            payload_file_path: The path to the payload file.
            save_to_ctx: save the result to context or not.
        Some exceptions could be raised while invoking the serverless function.
        """

        with open(payload_file_path) as f:
            payload = f.read()

        # check if the actual memory value is equal to memory_mb, otherwise sets it
        self.check_and_set_memory_value(memory_mb)
        is_memory_config_ok = False

        while True:
            results = {key: [] for key in self.log_keys}
            errors = []
            enomem = False

            # invocation chunks is the number of invocation that must be considered for a given mem value,
            # and it is a list of the number of invocation for each thread, last item in the list is the remainder
            invocation_chunks = [invocation_count // nbr_threads] * nbr_threads
            invocation_chunks[-1] += (
                invocation_count - invocation_count // nbr_threads * nbr_threads
            )

            with ThreadPoolExecutor(max_workers=nbr_threads) as executor:
                try:
                    futures = [
                        executor.submit(
                            self.invoke_sequential, count=chunk, payload=payload
                        )
                        for chunk in invocation_chunks
                    ]
                except SingleInvocationError as e:
                    errors.append(e.msg)
                    continue
                except LambdaTimeoutError:
                    errors.append("Lambda timed out")
                    enomem = True
                    continue
                except LambdaENOMEM:
                    enomem = True
                    break
                except botocore.exceptions.ReadTimeoutError:
                    errors.append("Lambda timed out")
                    continue
                for future in as_completed(futures):
                    res = future.result()
                    for key in self.log_keys:
                        results[key].extend(res[key])

            print(f"The results: {results}")
            if enomem:
                raise LambdaENOMEM
            if all([m == memory_mb for m in results["Memory Size"]]):
                is_memory_config_ok = True
                break

        # Ashia said this not to be used anymore
        if not is_memory_config_ok:
            raise LambdaMemoryConfigError

        if len(errors) != 0:
            raise LambdaInvocationError(errors)

        result_df = pd.DataFrame.from_dict(results)
        if save_to_ctx:
            self.context.save_invocation_result(result_df)

        durations = results["Billed Duration"]
        cached_df = pd.DataFrame(
            {
                "duration": durations,
                "function_name": [self.function_name] * len(durations),
                "memory": [memory_mb] * len(durations),
            }
        )
        self.context.record_cached_data(cached_df)
        return result_df

    @abstractmethod
    def check_and_set_memory_value(self, memory_mb):
        pass

    @abstractmethod
    def invoke_sequential(self, count: int, payload: str):
        pass
