import base64
from unittest import mock

import pytest
from botocore.exceptions import *

from src.configuration import defaults
from src.exception import *
from src.exploration.aws.aws_invoker import AWSInvoker


@pytest.fixture
def invoker():
    # Mock the AWS session and client objects.
    mock_aws_session = mock.Mock()
    mock_aws_session.client().invoke.return_value = {
        "LogResult": "XHREdXJhdGlvbjogMTcwLjI0IG1zXHRCaWxsZWQgRHVyYXRpb246IDE3MSBtc1x0TWVtb3J5IFNpemU6IDEyOCBNQlx0TWF4I"
        "E1lbW9yeSBVc2VkOiA0MCBNQlx0SW5pdCBEdXJhdGlvbjogMTM0LjcwIG1zXHRcbiI="
    }
    return AWSInvoker(
        function_name="example_function",
        max_invocation_attempts=5,
        aws_session=mock_aws_session,
    )


class TestInvoke:
    def test_nominal_case(self, invoker):
        response = invoker.invoke(payload="payload")
        expected = "b'\\\\tDuration: 170.24 ms\\\\tBilled Duration: 171 ms\\\\tMemory Size: 128 MB\\\\tMax Memory Used: 40 MB\\\\tInit Duration: 134.70 ms\\\\t\\\\n\"'"

        assert response == expected

    def test_client_error(self, invoker):
        mock_error_response = {
            "Error": {
                "Message": "Function not found: arn:aws:lambda:us-east-1:880306299867:function:function_not_found",
                "Code": "ResourceNotFoundException",
            },
        }
        invoker.client.invoke = mock.Mock()
        invoker.client.invoke.side_effect = ClientError(
            operation_name="GetFunctionConfiguration",
            error_response=mock_error_response,
        )

        with pytest.raises(InvocationError) as error:
            invoker.invoke(payload="payload")

        assert error.type == InvocationError

    @mock.patch("src.exploration.aws.aws_invoker.time.sleep")
    def test_max_number_of_invocations_attempts_reached_error(self, sleep, invoker):
        invoker.client.invoke = mock.Mock(
            side_effect=(
                Exception() for _ in range(defaults.MAX_NUMBER_OF_INVOCATION_ATTEMPTS)
            )
        )

        with pytest.raises(MaxInvocationAttemptsReachedError) as error:
            invoker.invoke(payload="payload")

        assert error.type == MaxInvocationAttemptsReachedError
        assert (
            invoker.client.invoke.call_count == defaults.MAX_NUMBER_OF_INVOCATION_ATTEMPTS
        )

    @mock.patch("src.exploration.aws.aws_invoker.time.sleep")
    def test_handling_aws_throttling(self, sleep, invoker):
        response = {"LogResult": "VGVzdCByZXNwb25zZQ=="}
        invoker.client.invoke = mock.Mock(
            side_effect=(Exception(), Exception(), response)
        )

        invoker.invoke(payload="payload")

        assert invoker.client.invoke.call_count == 3

    def test_read_time_out(self, invoker):
        # Arrange
        invoker.client.invoke = mock.Mock(
            side_effect=(
                ReadTimeoutError(endpoint_url="endpoint"),
                {"LogResult": base64.b64encode(b"result")},
            )
        )

        # Action
        invoker.invoke(payload="payload")

        # Assert
        assert invoker.client.invoke.call_count == 2
