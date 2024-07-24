import time

import boto3
from botocore.exceptions import *

from src.exception import *
from src.exploration.config_manager import ConfigManager
from src.exploration.function_config import FunctionConfig
from src.logger import logger


class AWSConfigManager(ConfigManager):
    def __init__(self, function_name: str, aws_session: boto3.Session):
        super().__init__(function_name)
        self._lambda_client = aws_session.client("lambda")
        self._quotas_client = aws_session.client("service-quotas")

    @property
    def max_timeout_quota(self) -> int:
        # try:
        #     # Get the account's timeout quota if configured by the user.
        #     quota = self._quotas_client.get_service_quota(
        #         ServiceCode="lambda", QuotaCode="L-9FEEFFC0"
        #     )
        #
        # except ClientError:
        #     # Get the default timeout quota.
        #     quota = self._quotas_client.get_aws_default_service_quota(
        #         ServiceCode="lambda", QuotaCode="L-9FEEFFC0"
        #     )
        #
        # return int(quota["Quota"]["Value"])
        return 900

    def set_config(self, memory_mb: int, timeout: int = None) -> any:
        sleeping_interval = 1
        try:
            config = self._lambda_client.get_function_configuration(
                FunctionName=self.function_name
            )

            if not self.initial_config:
                self.initial_config = FunctionConfig(
                    config["MemorySize"], config["Timeout"]
                )

            # Update the lambda function's configuration.
            if timeout:
                self._lambda_client.update_function_configuration(
                    FunctionName=self.function_name,
                    MemorySize=int(memory_mb),
                    Timeout=timeout,
                )
            else:
                self._lambda_client.update_function_configuration(
                    FunctionName=self.function_name,
                    MemorySize=int(memory_mb),
                    Timeout=self.max_timeout_quota,
                )

            # Wait until configuration is propagated to all worker instances.
            while (
                    config["MemorySize"] != memory_mb
                    or config["LastUpdateStatus"] == "InProgress"
            ):
                # Wait for the lambda function's status has changed to "UPDATED".
                waiter = self._lambda_client.get_waiter("function_updated")
                waiter.wait(FunctionName=self.function_name)

                config = self._lambda_client.get_function_configuration(
                    FunctionName=self.function_name
                )

        except ParamValidationError as e:
            logger.debug(e.args[0])
            raise FunctionConfigError(e.args[0])

        except ClientError as e:
            logger.debug(e.args[0])

            # Retry if function is being updated now
            if e.response['Error']['Code'] == 'ResourceConflictException':
                logger.warning("Concurrent Update Function Error. Retrying ...")

                # Exponential retry interval
                time.sleep(sleeping_interval)
                sleeping_interval *= 2

                self.set_config(memory_mb, timeout)

            else:
                raise FunctionConfigError(e.args[0])

        else:
            return config
