import base64
import sys
import time
from botocore.exceptions import *
import spot.constants as const
from spot.invocation.logs_parsing import *
from ..exceptions import *
from . import FunctionInvoker


class AWSLambdaInvoker(FunctionInvoker):
    """Implementation of the FunctionInvoker for AWS Lambda functions.

    This class provides the operation to invoke the AWS lambda function with a specific configuration multiple times.
    """

    def __init__(self, lambda_name: str, client: any):
        super().__init__(
            function_name=lambda_name,
            log_parser=AWSLogParser(),
        )
        self.client = client

    def execute_and_parse_logs(self, payload: str) -> tuple:
        """For a fixed configuration invokes the Lambda function sequentially multiple times with the same payload
        and returns parsed logs_parsing.

        Args:
            payload (str): The payload to pass to the Lambda function for each invocation.

        Returns:
            tuple: A tuple containing the invocation results (str), and a list of errors (list).

        Raises:
            LambdaENOMEM: If the memory configuration is not sufficient for lambda execution.
        """
        # TODO: maybe support different payload across invocations?

        result = {key: [] for key in self.log_parser.log_parsing_keys}
        errors = []

        try:
            response = self._execute_lambda(payload)
        except MaxNumberInvocationAttemptsReachedError as e:
            print(e)
            exit(1)

        try:
            parsed_log = self.log_parser.parse_log(response)
        except SingleInvocationError as e:
            errors.append(e)
        except LambdaTimeoutError as e:
            errors.append(e)
            raise LambdaENOMEM
        except ReadTimeoutError:
            errors.append("Lambda invocation timed out. The API request to the AWS Lambda service, took longer than "
                          "the specified timeout period.")
        else:
            for key in self.log_parser.log_parsing_keys:
                result[key].append(parsed_log[key])

        return result, errors

    def _execute_lambda(self, payload: str) -> str:
        """Invokes the Lambda function once with the given payload and return the logs_parsing returned by AWS Lambda.

        Args:
            payload (str): The payload to invoke the function with.

        Returns:
            str: The logs_parsing returned by AWS Lambda in response to the invocation.

        Raises:
            MaxNumberInvocationAttemptsReachedError: If the maximum number of invocation attempts is reached.
        """
        sleeping_interval = 1
        for _ in range(const.MAX_NUMBER_INVOCATION_ATTEMPTS):
            try:
                # Invoking the function and getting back the response log to parse.
                response = self.client.invoke(
                    FunctionName=self.function_name,
                    LogType="Tail",
                    Payload=payload,
                )

            except ClientError:
                print("Error has been raised while invoking the lambda function. "
                      "Please make sure that the provided function name and configuration are correct!")
                exit(1)

            except Exception:
                # Handling the throttling imposed by AWS on the number of concurrent executions.
                print("Possibly Too Many Requests Error. Retrying...", file=sys.stderr)
                time.sleep(sleeping_interval)
                sleeping_interval *= 2

            else:
                return str(base64.b64decode(response["LogResult"]))

        raise MaxNumberInvocationAttemptsReachedError

    def check_and_set_memory_value(self, memory_mb: int) -> dict:
        """Checking and setting the configuration memory value of the lambda function.

        Args:
            memory_mb (int): The memory size in MB.

        Returns:
            dict: the retrieved configuration of the lambda function.
        """
        try:
            config = self.client.get_function_configuration(FunctionName=self.function_name)

            while config["MemorySize"] != memory_mb:
                # Update the lambda function configuration.
                self.client.update_function_configuration(FunctionName=self.function_name, MemorySize=memory_mb)
                waiter = self.client.get_waiter("function_updated")
                waiter.wait(FunctionName=self.function_name)
                config = self.client.get_function_configuration(FunctionName=self.function_name)

        except ClientError:
            print("Lambda function not found. Please make sure that the provided function name "
                  "and configuration are correct!")
            exit(1)

        else:
            return config
