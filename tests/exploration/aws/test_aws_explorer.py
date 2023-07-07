import base64
from unittest import mock

import pytest
from botocore.exceptions import *

import src.constants as const
from src.exceptions import *
from src.exploration.aws import AWSExplorer


@pytest.fixture
def explorer():
    # Mock the AWS session and client objects.
    mock_aws_session = mock.Mock()

    # Configure the mock objects to return the expected values.
    mock_aws_session.client.return_value = mock.Mock()

    mock_aws_session.client().invoke.return_value = {
        "LogResult": "XHREdXJhdGlvbjogMTcwLjI0IG1zXHRCaWxsZWQgRHVyYXRpb246IDE3MSBtc1x0TWVtb3J5IFNpemU6IDEyOCBNQlx0TWF4I"
        "E1lbW9yeSBVc2VkOiA0MCBNQlx0SW5pdCBEdXJhdGlvbjogMTM0LjcwIG1zXHRcbiI="
    }

    mock_aws_session.client().get_function_configuration.return_value = {
        "MemorySize": 256,
        "LastUpdateStatus": "Successful",
    }

    def mock_update_function_configuration(FunctionName: str, MemorySize: int):
        mock_aws_session.client().get_function_configuration.side_effect = (
            {"MemorySize": MemorySize, "LastUpdateStatus": "InProgress"},
            {"MemorySize": MemorySize, "LastUpdateStatus": "Successful"},
        )

    mock_aws_session.client().update_function_configuration = (
        mock_update_function_configuration
    )

    return AWSExplorer(
        lambda_name="example_function",
        payload="payload",
        max_invocation_attempts=5,
        aws_session=mock_aws_session,
    )


class TestCheckAndSetMemoryValue:
    def test_update_memory(self, explorer):
        config = explorer.check_and_set_memory_config(128)

        assert config["MemorySize"] == 128

    def test_param_value_error(self, explorer):
        explorer.client.update_function_configuration = mock.Mock(
            side_effect=ParamValidationError(report="error")
        )

        with pytest.raises(MemoryConfigError) as error:
            explorer.check_and_set_memory_config("wrong parm")
        assert error.type == MemoryConfigError

    def test_function_not_found(self, explorer):
        mock_error_response = {
            "Error": {
                "Message": "Function not found: arn:aws:lambda:us-east-1:880306299867:function:function_not_found",
                "Code": "ResourceNotFoundException",
            },
        }
        explorer.client.get_function_configuration = mock.Mock()
        explorer.client.get_function_configuration.side_effect = ClientError(
            operation_name="GetFunctionConfiguration",
            error_response=mock_error_response,
        )

        with pytest.raises(MemoryConfigError) as error:
            explorer.check_and_set_memory_config(128)
        assert error.type == MemoryConfigError


class Testinvoke:
    def test_nominal_case(self, explorer):
        response = explorer.invoke()
        expected = "b'\\\\tDuration: 170.24 ms\\\\tBilled Duration: 171 ms\\\\tMemory Size: 128 MB\\\\tMax Memory Used: 40 MB\\\\tInit Duration: 134.70 ms\\\\t\\\\n\"'"

        assert response == expected

    def test_client_error(self, explorer):
        mock_error_response = {
            "Error": {
                "Message": "Function not found: arn:aws:lambda:us-east-1:880306299867:function:function_not_found",
                "Code": "ResourceNotFoundException",
            },
        }
        explorer.client.invoke = mock.Mock()
        explorer.client.invoke.side_effect = ClientError(
            operation_name="GetFunctionConfiguration",
            error_response=mock_error_response,
        )

        with pytest.raises(InvocationError) as error:
            explorer.invoke()
        assert error.type == InvocationError

    @mock.patch("src.exploration.aws.aws_explorer.time.sleep")
    def test_max_number_of_invocations_attempts_reached_error(self, sleep, explorer):
        explorer.client.invoke = mock.Mock(
            side_effect=(
                Exception() for _ in range(const.MAX_NUMBER_INVOCATION_ATTEMPTS)
            )
        )

        with pytest.raises(InvocationError) as error:
            explorer.invoke()
        assert error.type == InvocationError
        assert explorer.client.invoke.call_count == const.MAX_NUMBER_INVOCATION_ATTEMPTS

    @mock.patch("src.exploration.aws.aws_explorer.time.sleep")
    def test_handling_aws_throttling(self, sleep, explorer):
        response = {"LogResult": "VGVzdCByZXNwb25zZQ=="}
        explorer.client.invoke = mock.Mock(
            side_effect=(Exception(), Exception(), response)
        )

        explorer.invoke()

        assert explorer.client.invoke.call_count == 3

    def test_read_time_out(self, explorer):
        # Arrange
        explorer.client.invoke = mock.Mock(
            side_effect=(
                ReadTimeoutError(endpoint_url="endpoint"),
                {"LogResult": base64.b64encode(b"result")},
            )
        )

        # Action
        explorer.invoke()

        # Assert
        assert explorer.client.invoke.call_count == 2
