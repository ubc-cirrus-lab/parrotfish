from unittest import mock

import pytest
from google.api_core.exceptions import GoogleAPICallError

from src.exceptions import *
from src.exploration import GCPExplorer


@pytest.fixture
def explorer():
    return GCPExplorer(function_name="example_function", payload="payload", project_id="project_id", region="region")


class TestCheckAndSetMemoryConfig:
    @mock.patch("src.exploration.gcp.gcp_explorer.functions_v1")
    def test_update_memory(self, functions_v1, explorer):
        # Arrange
        update_memory_size_mb = 128
        function = type('', (), {})()  # create an empty object that will serve to mock the get_function response
        function.available_memory_mb = 256  # patch the object
        explorer._function_client.get_function = mock.Mock(return_value=function)

        def mock_update_function(request):
            update_operation = mock.Mock()
            request["function"].available_memory_mb = update_memory_size_mb
            update_operation.result = mock.Mock(return_value=request["function"])
            return update_operation

        functions_v1.UpdateFunctionRequest = mock.Mock(return_value={"function": function})
        explorer._function_client.update_function = mock_update_function

        # Action
        config = explorer.check_and_set_memory_config(update_memory_size_mb)

        # Assert
        assert config.available_memory_mb == update_memory_size_mb

    def test_function_not_found_error(self, explorer):
        update_memory_size_mb = 128
        explorer._function_client.get_function = mock.Mock(side_effect=GoogleAPICallError("error"))

        with pytest.raises(MemoryConfigError) as e:
            explorer.check_and_set_memory_config(update_memory_size_mb)
        assert e.type == MemoryConfigError

    @mock.patch("src.exploration.gcp.gcp_explorer.functions_v1")
    def test_not_valid_memory_value(self, functions_v1, explorer):
        function = type('', (), {})()  # create an empty object that will serve to mock the get_function response
        function.available_memory_mb = 256  # patch the object
        explorer._function_client.get_function = mock.Mock(return_value=function)
        explorer._function_client.update_function = mock.Mock(side_effect=GoogleAPICallError("error"))

        with pytest.raises(MemoryConfigError) as e:
            explorer.check_and_set_memory_config(128)
        assert e.type == MemoryConfigError


class TestInvoke:
    def test_nominal_case(self, explorer):
        # Arrange
        result = type('', (), {})()
        result.execution_id = "execution_id"
        explorer._function_client.call_function = mock.Mock(return_value=result)
        expected_result = "finished execution"
        explorer._get_invocation_log = mock.Mock(return_value=expected_result)

        # Action
        response = explorer.invoke()

        # Assert
        assert response == expected_result

    def test_calling_error(self, explorer):
        explorer._function_client.call_function = mock.Mock(side_effect=GoogleAPICallError("error"))

        with pytest.raises(InvocationError) as e:
            explorer.invoke()
        assert e.type == InvocationError

    def test_list_logs_error(self, explorer):
        result = type('', (), {})()
        result.execution_id = "execution_id"
        explorer._function_client.call_function = mock.Mock(return_value=result)
        explorer._get_invocation_log = mock.Mock(side_effect=GoogleAPICallError("error"))

        with pytest.raises(InvocationError) as e:
            explorer.invoke()
        assert e.type == InvocationError


class TestGetInvocationLog:
    @staticmethod
    def create_log_object(payload):
        res = type('', (), {})()
        res.payload = payload
        return res

    @mock.patch("src.exploration.gcp.gcp_explorer.google_logging")
    @mock.patch("src.exploration.gcp.gcp_explorer.time.sleep")
    def test_nominal_case(self, sleep, logging, explorer):
        # Arrange
        entry_payload = "Function execution took 50 ms, finished with status code: 200"
        expected_log = "execid:" + entry_payload
        logging_client = mock.Mock()
        logging.Client = mock.Mock(return_value=logging_client)
        logs = [self.create_log_object(entry_payload)]
        logging_client.list_entries = mock.Mock(return_value=(i for i in logs))  # Mock to return a generator.

        # Action
        log = explorer._get_invocation_log("execid")

        # Assert
        assert log == expected_log
        assert logging.Client().list_entries.call_count == 1

    @mock.patch("src.exploration.gcp.gcp_explorer.google_logging")
    @mock.patch("src.exploration.gcp.gcp_explorer.time.sleep")
    def test_execution_time_not_in_first_log(self, sleep, logging, explorer):
        # Arrange
        entry_payload = "Function execution took 50 ms, finished with status code: 200"
        expected_log = "execid:" + entry_payload
        logs = ["log", entry_payload]
        logging_client = mock.Mock()
        logging.Client = mock.Mock(return_value=logging_client)
        logs = [self.create_log_object(log) for log in logs]
        logging_client.list_entries = mock.Mock(return_value=(i for i in logs))

        # Action
        log = explorer._get_invocation_log("execid")

        # Assert
        assert log == expected_log
        assert logging.Client().list_entries.call_count == 2
