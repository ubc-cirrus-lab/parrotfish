from unittest import mock

import pytest
from botocore.exceptions import *

from src.data_model import FunctionConfig
from src.exceptions import FunctionConfigError
from src.exploration.aws.aws_config_manager import AWSConfigManager


@pytest.fixture
def config_manager():
    # Mock the AWS session and client objects.
    mock_aws_session = mock.Mock()

    mock_aws_session.client.return_value = mock.Mock()
    mock_aws_session.client().get_function_configuration.return_value = {
        "MemorySize": 256,
        "Timeout": 30,
        "LastUpdateStatus": "Successful",
    }

    def mock_update_function_configuration(FunctionName: str, MemorySize: int, Timeout: int = None):
        if Timeout:
            mock_aws_session.client().get_function_configuration.side_effect = (
                {"MemorySize": MemorySize, "Timeout": 30, "LastUpdateStatus": "InProgress"},
                {"MemorySize": MemorySize, "Timeout": Timeout, "LastUpdateStatus": "Successful"},
            )
        else:
            mock_aws_session.client().get_function_configuration.side_effect = (
                {"MemorySize": MemorySize, "Timeout": 30, "LastUpdateStatus": "InProgress"},
                {"MemorySize": MemorySize, "Timeout": 30, "LastUpdateStatus": "Successful"},
            )

    mock_aws_session.client().update_function_configuration = mock_update_function_configuration
    mock_aws_session.client().get_service_quota = mock.Mock(return_value={'Quota': {'Value': 900}})

    return AWSConfigManager("example_function", mock_aws_session)


class TestSetConfig:
    def test_save_initial_config(self, config_manager):
        config_manager.set_config(128)

        assert config_manager.initial_config == FunctionConfig(memory_mb=256, timeout=30)

    def test_update_memory(self, config_manager):
        config = config_manager.set_config(128)

        assert config["MemorySize"] == 128
        assert config["Timeout"] == 900

    def test_update_timeout(self, config_manager):
        config = config_manager.set_config(128, 100)

        assert config["MemorySize"] == 128
        assert config["Timeout"] == 100

    def test_param_value_error(self, config_manager):
        config_manager._lambda_client.update_function_configuration = mock.Mock(
            side_effect=ParamValidationError(report="error")
        )

        with pytest.raises(FunctionConfigError) as error:
            config_manager.set_config(10)
        assert error.type == FunctionConfigError

    def test_function_not_found(self, config_manager):
        mock_error_response = {
            "Error": {
                "Message": "Function not found: arn:aws:lambda:us-east-1:880306299867:function:function_not_found",
                "Code": "ResourceNotFoundException",
            },
        }
        config_manager._lambda_client.get_function_configuration.side_effect = ClientError(
            operation_name="GetFunctionConfiguration",
            error_response=mock_error_response,
        )

        with pytest.raises(FunctionConfigError) as error:
            config_manager.set_config(128)
        assert error.type == FunctionConfigError
