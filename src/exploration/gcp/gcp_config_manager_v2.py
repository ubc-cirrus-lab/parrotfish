import datetime

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import functions_v2

from src.exception import FunctionConfigError
from src.exploration.config_manager import ConfigManager
from src.exploration.function_config_v2 import FunctionConfigV2
from src.logging import logger


class GCPConfigManagerV2(ConfigManager):
    def __init__(self, function_name: str, credentials: any):
        super().__init__(function_name)
        self.credentials = credentials
        self.project_id = credentials.project_id
        self.region = credentials.region
        self.function_url = f"projects/{self.project_id}/locations/{self.region}/functions/{function_name}"
        self._function_client = functions_v2.FunctionServiceClient(
            credentials=credentials
        )

    @property
    def max_timeout_quota(self) -> int:
        return 540
    
    def mb_to_bytes(self, mb):
        bytes_in_mb = 1024 * 1024
        return int(mb * bytes_in_mb)

    def set_config(self, memory_mb: int, timeout: int = None, cpu: float = None) -> any:
        try:
            function = self._function_client.get_function(name=self.function_url)

            if not self.initial_config:
                self.initial_config = FunctionConfigV2(
                    memory_mb if memory_mb is not None else 128, 
                    timeout if timeout is not None else 1500, 
                    cpu if cpu is not None else 0.08,
                )
            function.service_config.available_memory = str(self.mb_to_bytes(memory_mb))
            function.service_config.available_cpu = str(cpu)
            
            # Update the function configuration
            update_mask = {'paths': ['service_config.available_memory', 'service_config.available_cpu']}
            operation = self._function_client.update_function(function=function, update_mask=update_mask)
            
            # Wait for the update operation to complete
            response = operation.result()

        except GoogleAPICallError as e:
            logger.debug(e.args[0])
            raise FunctionConfigError

        else:
            return function
