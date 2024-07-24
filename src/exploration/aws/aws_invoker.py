import base64
import time

import boto3
from botocore.exceptions import *

from src.exception import *
from src.exploration.invoker import Invoker
from src.logger import logger


class AWSInvoker(Invoker):
    def __init__(
            self,
            function_name: str,
            max_invocation_attempts: int,
            aws_session: boto3.Session,
    ):
        super().__init__(function_name, max_invocation_attempts)
        self.client = aws_session.client("lambda")

    def _invoke_with_retry(self, payload: str) -> dict:
        sleeping_interval = 5
        for _ in range(10):
            try:
                # Invoking the function and getting back the response log to parse.
                memory_size = self.client.get_function_configuration(
                    FunctionName=self.function_name
                )["MemorySize"]

                logger.debug("Invoking function: " + self.function_name + " , Memory size: " + str(memory_size))

                response = self.client.invoke(
                    FunctionName=self.function_name, LogType="Tail", Payload=payload
                )
                return response

            except ClientError as e:
                if e.response["Error"]["Code"] == "TooManyRequestsException":
                    # Handling the throttling imposed by AWS on the number of concurrent executions.
                    logger.warning("Concurrent Invocation Limit Exceeded. Retrying ... Function: " + self.function_name
                                   + " Memory size: " + str(memory_size))

                    time.sleep(sleeping_interval)
                    sleeping_interval *= 2

                else:
                    logger.debug(e.args[0])
                    raise InvocationError(
                        "Error has been raised while invoking the lambda function. Please make sure "
                        "that the provided function name and configuration are correct!"
                    )

            except ReadTimeoutError:
                logger.warning(
                    "Lambda exploration timed out. The API request to the AWS Lambda service, "
                    "took longer than the specified timeout period. Retry ..."
                )
                return self._invoke_with_retry(payload)  # Retry again

            except ParamValidationError as e:
                raise InvocationError(e.args[0])

            except Exception:
                # Handling the throttling imposed by AWS on the number of concurrent executions.
                logger.warning("Possibly Too Many Requests Error. Retrying...")

                time.sleep(sleeping_interval)
                sleeping_interval *= 2

        logger.warning("MaxInvocationAttemptsReachedError" + self.function_name + str(memory_size))
        raise MaxInvocationAttemptsReachedError

    def invoke(self, payload: str) -> str:
        response = self._invoke_with_retry(payload)
        return str(base64.b64decode(response["LogResult"]))

    def invoke_for_output(self, payload: str) -> str:
        response = self._invoke_with_retry(payload)
        response_payload = response['Payload'].read().decode('utf-8')
        return response_payload
