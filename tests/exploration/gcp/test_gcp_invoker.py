from unittest import mock

import pytest
from google.api_core.exceptions import GoogleAPICallError

from src.exceptions import InvocationError
from src.exploration.gcp.gcp_invoker import GCPInvoker


@pytest.fixture
@mock.patch("src.exploration.gcp.gcp_invoker.functions_v1")
@mock.patch("src.exploration.gcp.gcp_invoker.google_logging")
def invoker(function_v1, google_logging):
    credentials = type("", (), {})()
    credentials.project_id = "example_project_id"
    credentials.region = "example_region"
    function_v1.CloudFunctionsServiceClient = mock.Mock()
    google_logging.Client = mock.Mock()
    return GCPInvoker(
        function_name="example_function",
        log_keys=["Function execution took", "finished with status"],
        credentials=credentials,
    )


class TestInvoke:
    def test_nominal_case(self, invoker):
        # Arrange
        result = type("", (), {})()
        result.execution_id = "execution_id"
        invoker._function_client.call_function = mock.Mock(return_value=result)
        expected_result = "finished execution"
        invoker._get_invocation_log = mock.Mock(return_value=expected_result)

        # Action
        response = invoker.invoke(payload="payload")

        # Assert
        assert response == expected_result

    def test_calling_error(self, invoker):
        invoker._function_client.call_function = mock.Mock(
            side_effect=GoogleAPICallError("error")
        )

        with pytest.raises(InvocationError) as e:
            invoker.invoke(payload="payload")

        assert e.type == InvocationError

    def test_list_logs_error(self, invoker):
        result = type("", (), {})()
        result.execution_id = "execution_id"
        invoker._function_client.call_function = mock.Mock(return_value=result)
        invoker._get_invocation_log = mock.Mock(side_effect=GoogleAPICallError("error"))

        with pytest.raises(InvocationError) as e:
            invoker.invoke(payload="payload")
        assert e.type == InvocationError


class TestGetInvocationLog:
    @staticmethod
    def create_log_object(payload):
        res = type("", (), {})()
        res.payload = payload
        return res

    @mock.patch("src.exploration.gcp.gcp_invoker.time")
    def test_nominal_case(self, time, invoker):
        # Arrange
        time.sleep = mock.Mock()
        entry_payload = "Function execution took 50 ms, finished with status code: 200"
        expected_log = "execid:" + entry_payload + "\n"
        invoker._logging_client = mock.Mock()
        logs = [self.create_log_object(entry_payload)]
        invoker._logging_client.list_entries = mock.Mock(
            return_value=(i for i in logs)
        )  # Mock to return a generator.

        # Action
        log = invoker._get_invocation_log("execid")

        # Assert
        assert log == expected_log
        assert invoker._logging_client.list_entries.call_count == 1

    @mock.patch("src.exploration.gcp.gcp_invoker.time")
    def test_execution_time_not_in_first_log(self, time, invoker):
        # Arrange
        time.sleep = mock.Mock()
        entry_payload = "Function execution took 50 ms, finished with status code: 200"
        expected_log = "execid:log\n" + entry_payload + "\n"
        logs = ["log", entry_payload]
        invoker._logging_client = mock.Mock()
        logs = [self.create_log_object(log) for log in logs]
        invoker._logging_client.list_entries = mock.Mock(return_value=(i for i in logs))

        # Action
        log = invoker._get_invocation_log("execid")

        # Assert
        assert log == expected_log
        assert invoker._logging_client.list_entries.call_count == 1
