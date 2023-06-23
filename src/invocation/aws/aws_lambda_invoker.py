import base64
import sys
import time
from botocore.exceptions import *
from botocore.client import BaseClient

import src.constants as const
from .aws_log_parser import AWSLogParser
from src.invocation import FunctionInvoker
from src.exceptions import *


class AWSLambdaInvoker(FunctionInvoker):
    """Implementation of the ServerlessFunctionInvoker for AWS Lambda functions.

    This class provides the operation to invoke the AWS lambda function with a specific configuration parallely
    multiple times.
    """

    def __init__(self, lambda_name: str, client: BaseClient):
        super().__init__(function_name=lambda_name, log_parser=AWSLogParser())
        self.client = client

    def check_and_set_memory_value(self, memory_mb: int) -> dict:
        """Checks if the configured memory value is equal to @memory_mb and if no match it will update the function's
        configuration by setting the memory value to @memory_mb.

        Args:
            memory_mb (int): The memory size in MB.

        Returns:
            dict: The retrieved configuration of the lambda function.

        Raises:
            FunctionMemoryConfigError: If checking or updating the lambda function's memory configuration fails.
        """
        try:
            config = self.client.get_function_configuration(FunctionName=self.function_name)

            # Update the lambda function's configuration.
            self.client.update_function_configuration(FunctionName=self.function_name, MemorySize=memory_mb)

            # Wait until configuration is propagated to all worker instances.
            while config["MemorySize"] != memory_mb or config["LastUpdateStatus"] == "InProgress":
                # Wait for the lambda function's status has changed to "UPDATED".
                waiter = self.client.get_waiter("function_updated")
                waiter.wait(FunctionName=self.function_name)

                config = self.client.get_function_configuration(FunctionName=self.function_name)

        except ParamValidationError as e:
            raise FunctionMemoryConfigError(e.args[0])

        except ClientError:
            raise FunctionMemoryConfigError("Lambda function not found. Please make sure that the provided function "
                                            "name and configuration are correct!")

        else:
            return config

    def execute_function(self, payload: str) -> str:
        """Invokes the Lambda function with the payload @payload and returns the response base64 decoded.

        Args:
            payload (str): Payload to invoke the function with.

        Returns:
            str: The logs returned by AWS Lambda in response to the invocation. Logs are base64 decoded.

        Raises:
            InvocationError: If the invocation cannot be performed. (Possibly lambda function not found, user not
            authorised, or payload is wrong ...), or if the maximum number of invocation's attempts is reached.
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
                raise InvocationError("Error has been raised while invoking the lambda function. Please make sure "
                                      "that the provided function name and configuration are correct!")

            except Exception:
                # Handling the throttling imposed by AWS on the number of concurrent executions.
                print("Possibly Too Many Requests Error. Retrying...", file=sys.stderr)
                time.sleep(sleeping_interval)
                sleeping_interval *= 2

            else:
                return str(base64.b64decode(response["LogResult"]))

        raise InvocationError("Error has been raised while invoking the lambda function. Max number of invocations' "
                              "attempts reached.")
