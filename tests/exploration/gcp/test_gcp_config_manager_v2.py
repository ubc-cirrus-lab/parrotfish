import pytest
from unittest import mock

from google.api_core.exceptions import GoogleAPICallError
from src.exception import FunctionConfigError

from src.exploration.gcp.gcp_config_manager_v2 import GCPConfigManagerV2

@pytest.fixture
def config_manager_v2():
    credentials = type("", (), {})()
    credentials.project_id = "example_project_id"
    credentials.region = "example_region"
    return GCPConfigManagerV2("example_function", credentials)

class TestSetConfig:
    @mock.patch("src.exploration.gcp.gcp_config_manager_v2.functions_v2")
    def test_update(self, functions_v2, config_manager_v2):
        # Arrange
        update_cpu_size = 0.21
        update_memory_size_mb = 256
        function = type(
            "", (), {}
        )()  # create an empty object that will serve to mock the get_function response
        function.service_config = type("", (), {})()
        function.service_config.available_memory = config_manager_v2.mb_to_bytes(128)
        function.service_config.available_cpu = 0.08
        config_manager_v2._function_client.get_function = mock.Mock(return_value=function)

        def mock_update_function(function=None, update_mask=None):
            update_operation = mock.Mock()
            function.service_config.available_memory = str(
                config_manager_v2.mb_to_bytes(update_memory_size_mb)
            )
            function.service_config.available_cpu = str(update_cpu_size)
            update_operation.result = mock.Mock(return_value=function)
            return update_operation

        functions_v2.UpdateFunctionRequest = mock.Mock(
            return_value={"function": function}
        )
        config_manager_v2._function_client.update_function = mock_update_function

        # Action
        config = config_manager_v2.set_config(update_memory_size_mb, cpu=update_cpu_size)

        # Assert
        assert int(config.service_config.available_memory) == config_manager_v2.mb_to_bytes(update_memory_size_mb)
        assert float(config.service_config.available_cpu) == update_cpu_size

    def test_function_not_found_error(self, config_manager_v2):
        update_memory_size_mb = 256
        config_manager_v2._function_client.get_function = mock.Mock(
            side_effect=GoogleAPICallError("error")
        )

        with pytest.raises(FunctionConfigError) as e:
            config_manager_v2.set_config(update_memory_size_mb)
        assert e.type == FunctionConfigError
