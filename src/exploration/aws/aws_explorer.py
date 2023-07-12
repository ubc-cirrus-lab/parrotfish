import base64
import logging
import time

import boto3
from botocore.exceptions import *

from src.exceptions import *
from ..explorer import Explorer
from .aws_cost_calculator import AWSCostCalculator
from .aws_log_parser import AWSLogParser


class AWSExplorer(Explorer):
    def __init__(
        self,
        lambda_name: str,
        payload: str,
        max_invocation_attempts: int,
        aws_session: boto3.Session,
        memory_bounds: list = None,
    ):
        super().__init__(
            function_name=lambda_name,
            payload=payload,
            memory_bounds=memory_bounds,
            memory_space=set(range(128, 3008)),
            log_parser=AWSLogParser(),
            price_calculator=AWSCostCalculator(
                function_name=lambda_name, aws_session=aws_session
            ),
        )
        self._max_invocation_attempts = max_invocation_attempts
        self.client = aws_session.client("lambda")
        self._logger = logging.getLogger(__name__)

    def check_and_set_memory_config(self, memory_mb: int) -> dict:
        try:
            config = self.client.get_function_configuration(
                FunctionName=self.function_name
            )

            # Update the lambda function's configuration.
            self.client.update_function_configuration(
                FunctionName=self.function_name, MemorySize=memory_mb
            )

            # Wait until configuration is propagated to all worker instances.
            while (
                config["MemorySize"] != memory_mb
                or config["LastUpdateStatus"] == "InProgress"
            ):
                # Wait for the lambda function's status has changed to "UPDATED".
                waiter = self.client.get_waiter("function_updated")
                waiter.wait(FunctionName=self.function_name)

                config = self.client.get_function_configuration(
                    FunctionName=self.function_name
                )

        except ParamValidationError as e:
            raise MemoryConfigError(e.args[0])

        except ClientError as e:
            self._logger.debug(e.args[0])
            raise MemoryConfigError

        else:
            return config

    def invoke(self) -> str:
        sleeping_interval = 1
        for _ in range(self._max_invocation_attempts):
            try:
                # Invoking the function and getting back the response log to parse.
                response = self.client.invoke(
                    FunctionName=self.function_name,
                    LogType="Tail",
                    Payload=self.payload,
                )

            except ClientError as e:
                self._logger.debug(e)
                raise InvocationError(
                    "Error has been raised while invoking the lambda function. Please make sure "
                    "that the provided function name and configuration are correct!"
                )

            except ReadTimeoutError:
                self._logger.warn(
                    "Lambda exploration timed out. The API request to the AWS Lambda service, "
                    "took longer than the specified timeout period. Retry ..."
                )
                return self.invoke()  # Retry again

            except Exception:
                # Handling the throttling imposed by AWS on the number of concurrent executions.
                self._logger.warning("Possibly Too Many Requests Error. Retrying...")

                time.sleep(sleeping_interval)
                sleeping_interval *= 2

            else:
                return str(base64.b64decode(response["LogResult"]))

        raise InvocationError(
            "Error has been raised while invoking the lambda function. Max number of invocations' "
            "attempts reached."
        )
