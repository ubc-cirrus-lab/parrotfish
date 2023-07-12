import logging
import time

from google.api_core.exceptions import GoogleAPICallError, ResourceExhausted
from google.cloud import functions_v1
from google.cloud import logging as google_logging

from src.exceptions import *
from .gcp_cost_calculator import GCPCostCalculator
from .gcp_log_parser import GCPLogParser
from ..explorer import Explorer


class GCPExplorer(Explorer):
    def __init__(self, function_name: str, payload: str, credentials: any, memory_bounds: list = None):
        super().__init__(
            function_name=function_name,
            payload=payload,
            log_parser=GCPLogParser(),
            price_calculator=GCPCostCalculator(function_name=function_name, region=credentials.region),
            memory_space=set([2 ** i for i in range(7, 14)]),
            memory_bounds=memory_bounds
        )
        self.credentials = credentials
        self.project_id = credentials.project_id
        self.region = credentials.region
        self.function_url = f"projects/{self.project_id}/locations/{self.region}/functions/{function_name}"
        self._function_client = functions_v1.CloudFunctionsServiceClient(credentials=credentials)
        self._logger = logging.getLogger(__name__)

    def check_and_set_memory_config(self, memory_mb: int) -> any:
        try:
            function = self._function_client.get_function(name=self.function_url)

            if function.available_memory_mb != memory_mb:

                function.available_memory_mb = memory_mb
                update_mask = {"paths": ["available_memory_mb"]}
                request = functions_v1.UpdateFunctionRequest(function=function, update_mask=update_mask)

                update_operation = self._function_client.update_function(request)
                function = update_operation.result()

        except GoogleAPICallError as e:
            self._logger.debug(e.args[0])
            raise MemoryConfigError

        else:
            return function

    def invoke(self) -> str:
        try:
            response = self._function_client.call_function(name=self.function_url, data=self.payload)
            return self._get_invocation_log(response.execution_id)

        except GoogleAPICallError as e:
            self._logger.debug(e.args[0])
            raise InvocationError(e.args[0])

    def _get_invocation_log(self, execution_id: str) -> str:
        """Gets the invocation's log that contains the execution time value.

        Args:
            execution_id (str): The execution id of the cloud function.

        Returns:
            str: Invocation's log that contains execution time value.

        Retrieves the Cloud function invocation's logs and returns only the log that contains execution time value.
        """
        logging_client = google_logging.Client(credentials=self.credentials, project=self.project_id)
        filter_str = (
            f'resource.type="cloud_function"'
            f' AND resource.labels.function_name="{self.function_name}"'
            f' AND resource.labels.region="{self.region}"'
            f' AND labels.execution_id="{execution_id}"'
        )
        log = ''
        sleep_interval = 1

        while any([key not in log for key in self.log_parser.log_parsing_keys]):
            log = ''  # reset the log result

            try:
                # Retrieve the most recent logs
                entries = logging_client.list_entries(filter_=filter_str, order_by=google_logging.DESCENDING)
                log = f"{execution_id}:{next(entries).payload}"

            except StopIteration:
                self._logger.debug("waiting for logs to be retrieved.")
                time.sleep(15)  # wait for logs to be updated

            except ResourceExhausted as e:
                # Handling the cloud function's throttling.
                self._logger.debug(e.args[0])
                time.sleep(sleep_interval)
                sleep_interval *= 2

        return log
