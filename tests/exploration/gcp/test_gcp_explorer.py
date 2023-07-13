from unittest import mock

import pytest
from google.api_core.exceptions import GoogleAPICallError

from src.exceptions import *
from src.exploration import GCPExplorer


@pytest.fixture
def explorer():
    credentials = type("", (), {})()
    credentials.project_id = "example_project_id"
    credentials.region = "example_region"
    return GCPExplorer(
        function_name="example_function", payload="payload", credentials=credentials
    )


class TestCheckAndSetMemoryConfig:
    @mock.patch("src.exploration.gcp.gcp_explorer.functions_v1")
    def test_update_memory(self, functions_v1, explorer):
        # Arrange
        update_memory_size_mb = 128
        function = type(
            "", (), {}
        )()  # create an empty object that will serve to mock the get_function response
        function.available_memory_mb = 256  # patch the object
        explorer._function_client.get_function = mock.Mock(return_value=function)

        def mock_update_function(request):
            update_operation = mock.Mock()
            request["function"].available_memory_mb = update_memory_size_mb
            update_operation.result = mock.Mock(return_value=request["function"])
            return update_operation

        functions_v1.UpdateFunctionRequest = mock.Mock(
            return_value={"function": function}
        )
        explorer._function_client.update_function = mock_update_function

        # Action
        config = explorer.check_and_set_memory_config(update_memory_size_mb)

        # Assert
        assert config.available_memory_mb == update_memory_size_mb

    def test_function_not_found_error(self, explorer):
        update_memory_size_mb = 128
        explorer._function_client.get_function = mock.Mock(
            side_effect=GoogleAPICallError("error")
        )

        with pytest.raises(MemoryConfigError) as e:
            explorer.check_and_set_memory_config(update_memory_size_mb)
        assert e.type == MemoryConfigError

    @mock.patch("src.exploration.gcp.gcp_explorer.functions_v1")
    def test_not_valid_memory_value(self, functions_v1, explorer):
        function = type(
            "", (), {}
        )()  # create an empty object that will serve to mock the get_function response
        function.available_memory_mb = 256  # patch the object
        explorer._function_client.get_function = mock.Mock(return_value=function)
        explorer._function_client.update_function = mock.Mock(
            side_effect=GoogleAPICallError("error")
        )

        with pytest.raises(MemoryConfigError) as e:
            explorer.check_and_set_memory_config(128)
        assert e.type == MemoryConfigError


class TestInvoke:
    def test_nominal_case(self, explorer):
        # Arrange
        result = type("", (), {})()
        result.execution_id = "execution_id"
        explorer._function_client.call_function = mock.Mock(return_value=result)
        expected_result = "finished execution"
        explorer._get_invocation_log = mock.Mock(return_value=expected_result)

        # Action
        response = explorer.invoke()

        # Assert
        assert response == expected_result

    def test_calling_error(self, explorer):
        explorer._function_client.call_function = mock.Mock(
            side_effect=GoogleAPICallError("error")
        )

        with pytest.raises(InvocationError) as e:
            explorer.invoke()
        assert e.type == InvocationError

    def test_list_logs_error(self, explorer):
        result = type("", (), {})()
        result.execution_id = "execution_id"
        explorer._function_client.call_function = mock.Mock(return_value=result)
        explorer._get_invocation_log = mock.Mock(
            side_effect=GoogleAPICallError("error")
        )

        with pytest.raises(InvocationError) as e:
            explorer.invoke()
        assert e.type == InvocationError


class TestGetInvocationLog:
    @staticmethod
    def create_log_object(payload):
        res = type("", (), {})()
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
        logging_client.list_entries = mock.Mock(
            return_value=(i for i in logs)
        )  # Mock to return a generator.

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


class TestExplore:
    @pytest.fixture
    def gcp_explorer(self, explorer):
        explorer.check_and_set_memory_config = mock.Mock()
        explorer.invoke = mock.Mock()
        explorer.log_parser.parse_log = mock.Mock(return_value=18180)
        explorer.price_calculator.calculate_price = mock.Mock(return_value=10)
        return explorer

    def test_nominal_case(self, gcp_explorer):
        duration_ms = gcp_explorer.explore()

        assert gcp_explorer.price_calculator.calculate_price.called
        assert gcp_explorer.cost == 20
        assert duration_ms == 18180

    def test_check_and_set_memory_config_called(self, gcp_explorer):
        gcp_explorer.explore(memory_mb=128)

        assert gcp_explorer.check_and_set_memory_config.called

    def test_check_and_set_memory_config_raises_memory_config_error(self, gcp_explorer):
        gcp_explorer.check_and_set_memory_config = mock.Mock(
            side_effect=MemoryConfigError("error")
        )

        with pytest.raises(ExplorationError) as e:
            gcp_explorer.explore(memory_mb=128)
        assert e.type == MemoryConfigError

    def test_invocation_error_raised_by_invoke(self, gcp_explorer):
        gcp_explorer.invoke = mock.Mock(side_effect=InvocationError("error", 120))

        with pytest.raises(ExplorationError) as e:
            gcp_explorer.explore()
        assert e.type == InvocationError

    def test_invocation_error_raised_by_parse_log(self, gcp_explorer):
        gcp_explorer.log_parser.parse_log = mock.Mock(
            side_effect=InvocationError("error", 120)
        )

        with pytest.raises(ExplorationError) as e:
            gcp_explorer.explore()
        assert e.type == InvocationError

    @pytest.mark.parametrize(
        "error",
        [FunctionENOMEM(), FunctionTimeoutError()],
        ids=["FunctionENOMEM", "FunctionTimeoutError"],
    )
    def test_function_enomem(self, error, gcp_explorer):
        gcp_explorer.log_parser.parse_log = mock.Mock(side_effect=error)

        with pytest.raises(FunctionENOMEM) as e:
            gcp_explorer.explore()
        assert e.value == error

    def test_compute_cost_raises_cost_calculation_error(self, gcp_explorer):
        gcp_explorer.price_calculator.calculate_price = mock.Mock(
            side_effect=CostCalculationError("error")
        )

        with pytest.raises(ExplorationError) as e:
            gcp_explorer.explore(enable_cost_calculation=True)
        assert e.type == CostCalculationError
