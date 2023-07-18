import datetime
from unittest import mock

import pytest
from google.api_core.exceptions import GoogleAPICallError

from src.exceptions import FunctionConfigError
from src.exploration.gcp.gcp_config_manager import GCPConfigManager


@pytest.fixture
def config_manager():
    credentials = type("", (), {})()
    credentials.project_id = "example_project_id"
    credentials.region = "example_region"
    return GCPConfigManager("example_function", credentials)


class TestSetConfig:
    @mock.patch("src.exploration.gcp.gcp_config_manager.functions_v1")
    def test_update(self, functions_v1, config_manager):
        # Arrange
        update_memory_size_mb = 128
        update_timeout = datetime.timedelta(seconds=300)
        function = type(
            "", (), {}
        )()  # create an empty object that will serve to mock the get_function response
        function.available_memory_mb = 256  # patch the object
        function.timeout = update_timeout
        config_manager._function_client.get_function = mock.Mock(return_value=function)

        def mock_update_function(request):
            update_operation = mock.Mock()
            request["function"].available_memory_mb = update_memory_size_mb
            request["function"].timeout = update_timeout
            update_operation.result = mock.Mock(return_value=request["function"])
            return update_operation

        functions_v1.UpdateFunctionRequest = mock.Mock(
            return_value={"function": function}
        )
        config_manager._function_client.update_function = mock_update_function

        # Action
        config = config_manager.set_config(update_memory_size_mb)

        # Assert
        assert config.available_memory_mb == update_memory_size_mb
        assert config.timeout == update_timeout

    def test_function_not_found_error(self, config_manager):
        update_memory_size_mb = 128
        config_manager._function_client.get_function = mock.Mock(
            side_effect=GoogleAPICallError("error")
        )

        with pytest.raises(FunctionConfigError) as e:
            config_manager.set_config(update_memory_size_mb)
        assert e.type == FunctionConfigError

    @mock.patch("src.exploration.gcp.gcp_config_manager.functions_v1")
    def test_not_valid_memory_value(self, functions_v1, config_manager):
        function = type(
            "", (), {}
        )()  # create an empty object that will serve to mock the get_function response
        function.available_memory_mb = 256  # patch the object
        function.timeout = datetime.timedelta(seconds=300)  # patch the object
        config_manager._function_client.get_function = mock.Mock(return_value=function)
        config_manager._function_client.update_function = mock.Mock(
            side_effect=GoogleAPICallError("error")
        )

        with pytest.raises(FunctionConfigError) as e:
            config_manager.set_config(128)
        assert e.type == FunctionConfigError
