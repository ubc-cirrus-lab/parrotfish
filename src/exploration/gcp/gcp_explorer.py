import time

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import functions_v1
from google.cloud import logging

from src.exceptions import InvocationError
from src.exploration import Explorer
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
        function = self.function_client.get_function(name=self.function_url)
        if function.available_memory_mb == memory_mb:
            function.available_memory_mb = memory_mb

            update_mask = {"paths": ["available_memory_mb"]}
            request = functions_v1.UpdateFunctionRequest(function=function, update_mask=update_mask)
            update_operation = self.function_client.update_function(request)

            return update_operation.result()

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
            f'resource.type="cloud_function" AND resource.labels.function_name="{self.function_name}"'
            f' AND resource.labels.region="{self.region}" AND labels.execution_id="{execution_id}"'
        )
        res = ''

        while self.log_parser.log_parsing_keys[0] not in res:
            # Retrieve the logs
            logs = logging_client.list_entries(filter_=filter_str, order_by='timestamp desc')
            try:
                res = next(logs).payload
            except StopIteration:
                time.sleep(3)

        return res
