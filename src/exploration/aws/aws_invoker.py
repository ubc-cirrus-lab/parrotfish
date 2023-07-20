import base64
import logging
import time

import boto3
from botocore.exceptions import *

from src.exceptions import *
from src.exploration.invoker import Invoker


class AWSInvoker(Invoker):

    def __init__(
        self,
        function_name: str,
        max_invocation_attempts: int,
        aws_session: boto3.Session,
    ):
        super().__init__(function_name)
        self._max_invocation_attempts = max_invocation_attempts
        self.client = aws_session.client("lambda")

        self._logger = logging.getLogger(__name__)

    def invoke(self, payload: str) -> str:

        sleeping_interval = 1
        for _ in range(self._max_invocation_attempts):
            try:
                # Invoking the function and getting back the response log to parse.
                response = self.client.invoke(
                    FunctionName=self.function_name,
                    LogType="Tail",
                    Payload=payload,
                )

            except ClientError as e:
                self._logger.debug(e.args[0])
                raise InvocationError(
                    "Error has been raised while invoking the lambda function. Please make sure "
                    "that the provided function name and configuration are correct!"
                )

            except ReadTimeoutError:
                self._logger.warning(
                    "Lambda exploration timed out. The API request to the AWS Lambda service, "
                    "took longer than the specified timeout period. Retry ..."
                )
                return self.invoke(payload)  # Retry again

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
