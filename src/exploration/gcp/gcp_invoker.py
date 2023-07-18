import logging
import time

from google.api_core.exceptions import GoogleAPICallError, ResourceExhausted
from google.cloud import functions_v1
from google.cloud import logging as google_logging

from src.exceptions import *
from src.exploration.invoker import Invoker


class GCPInvoker(Invoker):

    def __init__(
        self, function_name: str, payload: str, log_keys: list, credentials: any
    ):
        super().__init__(function_name, payload)
        self.credentials = credentials
        self.project_id = credentials.project_id
        self.region = credentials.region
        self.function_url = f"projects/{self.project_id}/locations/{self.region}/functions/{function_name}"
        self._function_client = functions_v1.CloudFunctionsServiceClient(
            credentials=credentials,
        )
        self._logging_client = google_logging.Client(
            credentials=self.credentials, project=self.project_id
        )
        self.log_keys = log_keys
        self._logger = logging.getLogger(__name__)

    def invoke(self) -> str:
        try:
            response = self._function_client.call_function(
                name=self.function_url, data=self.payload
            )
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
        filter_str = (
            f'resource.type="cloud_function"'
            f' AND resource.labels.function_name="{self.function_name}"'
            f' AND resource.labels.region="{self.region}"'
            f' AND labels.execution_id="{execution_id}"'
        )
        log = ""
        sleep_interval = 1

        while any([key not in log for key in self.log_keys]):
            log = f"{execution_id}:"  # reset the log result

            try:
                # Retrieve the most recent logs
                entries = self._logging_client.list_entries(
                    filter_=filter_str, order_by=google_logging.DESCENDING
                )
                for entry in entries:
                    log += f"{entry.payload}\n"

            except StopIteration:
                self._logger.debug("waiting for logs to be retrieved.")
                time.sleep(15)  # wait for logs to be updated

            except ResourceExhausted as e:
                # Handling the cloud function's throttling.
                self._logger.debug(e.args[0])
                time.sleep(sleep_interval)
                sleep_interval *= 2

        return log
