import time

from google.api_core.exceptions import GoogleAPICallError, InvalidArgument
from google.cloud import functions_v1
from google.cloud import logging

from src.exceptions import *
from ..explorer import Explorer
from .gcp_cost_calculator import GCPCostCalculator
from .gcp_log_parser import GCPLogParser


class GCPExplorer(Explorer):
    def __init__(self, function_name: str, payload: str, project_id: str, region: str):
        super().__init__(
            function_name=function_name,
            payload=payload,
            log_parser=GCPLogParser(),
            price_calculator=GCPCostCalculator(function_name=function_name),
        )
        self.project_id = project_id
        self.region = region
        self.function_url = f"projects/{project_id}/locations/{region}/functions/{function_name}"
        self.function_client = functions_v1.CloudFunctionsServiceClient()

    def check_and_set_memory_config(self, memory_mb: int) -> any:
        try:
            function = self.function_client.get_function(name=self.function_url)

            if function.available_memory_mb != memory_mb:

                function.available_memory_mb = memory_mb
                update_mask = {"paths": ["available_memory_mb"]}
                request = functions_v1.UpdateFunctionRequest(function=function, update_mask=update_mask)

                update_operation = self.function_client.update_function(request)
                function = update_operation.result()

        except GoogleAPICallError as e:
            raise MemoryConfigError(e.args[0])

        else:
            return function

    def invoke(self) -> str:
        try:
            response = self.function_client.call_function(name=self.function_url, data=self.payload)
            return self._get_invocation_log(response.execution_id)

        except GoogleAPICallError as e:
            raise InvocationError(e.args[0])

    def _get_invocation_log(self, execution_id: str) -> str:
        """Gets the invocation's log that contains the execution time value.

        Args:
            execution_id (str): The execution id of the cloud function.

        Returns:
            str: Invocation's log that contains execution time value.

        Retrieves the Cloud function invocation's logs and returns only the log that contains execution time value.
        """
        logging_client = logging.Client(project=self.project_id)
        filter_str = (
            f'resource.type="cloud_function"'
            f' AND resource.labels.function_name="{self.function_name}"'
            f' AND resource.labels.region="{self.region}"'
            f' AND labels.execution_id="{execution_id}"'
        )
        log = ''

        while any([key not in log for key in self.log_parser.log_parsing_keys]):
            try:
                # Retrieve the most recent log
                result = logging_client.list_entries(filter_=filter_str, order_by='timestamp desc', page_size=1)
                log = next(result).payload
            except StopIteration:
                time.sleep(3)

        return log
