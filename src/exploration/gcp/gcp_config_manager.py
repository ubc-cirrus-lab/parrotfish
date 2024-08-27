import datetime

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import functions_v1

from src.exception import FunctionConfigError
from src.exploration.config_manager import ConfigManager
from src.exploration.function_config import FunctionConfig
from src.logging import logger


class GCPConfigManager(ConfigManager):
    def __init__(self, function_name: str, credentials: any):
        super().__init__(function_name)
        self.credentials = credentials
        self.project_id = credentials.project_id
        self.region = credentials.region
        self.function_url = f"projects/{self.project_id}/locations/{self.region}/functions/{function_name}"
        self._function_client = functions_v1.CloudFunctionsServiceClient(
            credentials=credentials
        )

    @property
    def max_timeout_quota(self) -> int:
        # TODO: Retrieve the timeout quota from the Google Cloud API.
        return 540

    def set_config(self, memory_mb: int, timeout: int = None, *args) -> any:
        try:
            function = self._function_client.get_function(name=self.function_url)

            if not self.initial_config:
                self.initial_config = FunctionConfig(
                    function.available_memory_mb, function.timeout.seconds
                )

            while function.available_memory_mb != memory_mb:
                # Update the memory configuration.
                function.available_memory_mb = memory_mb

                # Update the timeout configuration.
                if timeout:
                    function.timeout = datetime.timedelta(seconds=timeout)
                else:
                    function.timeout = datetime.timedelta(
                        seconds=self.max_timeout_quota
                    )

                # Apply updates to the Google Cloud Function.
                update_mask = {"paths": ["available_memory_mb", "timeout"]}
                request = functions_v1.UpdateFunctionRequest(
                    function=function, update_mask=update_mask
                )
                update_operation = self._function_client.update_function(request)
                function = (
                    update_operation.result()
                )  # Blocks until updates are applied.

        except GoogleAPICallError as e:
            logger.debug(e.args[0])
            raise FunctionConfigError

        else:
            return function
