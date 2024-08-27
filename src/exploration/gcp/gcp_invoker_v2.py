import time

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import functions_v2
from google.cloud import logging as google_logging
import requests
import json
from src.exception import *
from src.exploration.invoker import Invoker
from src.logger import logger


class GCPInvokerV2(Invoker):
    def __init__(
        self,
        function_name: str,
        max_invocation_attempts: int,
        credentials: any,
    ):
        super().__init__(function_name, max_invocation_attempts)
        self.credentials = credentials
        self.project_id = credentials.project_id
        self.region = credentials.region
        self.function_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net/{function_name}"
        self._function_client = functions_v2.FunctionServiceClient(
            credentials=credentials,
        )
        self._logging_client = google_logging.Client(
            credentials=self.credentials, project=self.project_id
        )

    def invoke(self, payload: str) -> int:
        sleeping_interval = 1
        for _ in range(self.max_invocation_attempts):
            try:
                response = requests.post(self.function_url, json=json.loads(payload))
                response.raise_for_status()
                return int(response.json()['response'] * 1000)

            except GoogleAPICallError as e:
                logger.debug(e.args[0])
                raise InvocationError(e.args[0])

            except Exception as e:
                logger.debug(e)
                logger.warning("Possibly Too Many Requests Error. Retrying...")

                time.sleep(sleeping_interval)
                sleeping_interval *= 2

        raise MaxInvocationAttemptsReachedError
