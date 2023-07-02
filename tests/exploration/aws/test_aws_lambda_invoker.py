import concurrent.futures

import boto3
import numpy as np
import pytest
from unittest import mock
from botocore.exceptions import *

import src.constants as const
from src.exploration.aws import AWSExplorer
from src.exceptions import *


@pytest.fixture
def invoker():
    client = mock.Mock()

    client.invoke.return_value = {
        "LogResult": "XHREdXJhdGlvbjogMTcwLjI0IG1zXHRCaWxsZWQgRHVyYXRpb246IDE3MSBtc1x0TWVtb3J5IFNpemU6IDEyOCBNQlx0TWF4I"
                     "E1lbW9yeSBVc2VkOiA0MCBNQlx0SW5pdCBEdXJhdGlvbjogMTM0LjcwIG1zXHRcbiI="
    }

    client.get_function_configuration.return_value = {"MemorySize": 256, "LastUpdateStatus": "Successful"}

    def mock_update_function_configuration(FunctionName: str, MemorySize: int):
        client.get_function_configuration.side_effect = (
            {"MemorySize": MemorySize, "LastUpdateStatus": "InProgress"},
            {"MemorySize": MemorySize, "LastUpdateStatus": "Successful"},
        )

    client.update_function_configuration = mock_update_function_configuration

    return AWSExplorer("example_function", client)


class TestInvoke:
    class MockFuture(concurrent.futures.Future):
        def __init__(self, result):
            super().__init__()
            self._result = result

        def result(self, timeout=None):
            return self._result

    def test_function_invocation_error(self, invoker):
        invoker.explore = mock.Mock(side_effect=ExplorationError("error"))

        with pytest.raises(ExplorationError) as e:
            invoker.explore_parallel(3, 3, 128, "payload")
        assert e.type == ExplorationError

    def test_lambda_enomem(self, invoker):
        invoker.explore = mock.Mock(side_effect=FunctionENOMEM)

        with pytest.raises(FunctionENOMEM) as e:
            invoker.explore_parallel(3, 3, 128, "payload")
        assert e.type == FunctionENOMEM

    @mock.patch("src.invocation.function_invoker.as_completed")
    @mock.patch("src.invocation.function_invoker.ThreadPoolExecutor")
    def test_parallel_execution(self, executor, as_completed, invoker):
        # Arrange
        def mock_submit(_, payload):
            pass
        executor.return_value.submit = mock_submit
        as_completed.return_value = [
            self.MockFuture({"Duration": 300, "Billed Duration": 300, "Max Memory Used": 100, "Memory Size": 128}),
            self.MockFuture({"Duration": 400, "Billed Duration": 400, "Max Memory Used": 90, "Memory Size": 128}),
            self.MockFuture({"Duration": 200, "Billed Duration": 200, "Max Memory Used": 120, "Memory Size": 128})
        ]
        expected = np.array([300, 400, 200])

        # Action
        results = invoker.explore_parallel(3, 3, 128, "payload")

        # Assert
        np.testing.assert_array_equal(results, expected)


class TestExecuteFunction:
    def test_nominal_case(self, invoker):
        response = invoker.invoke("payload")
        print(response)
        expected = b'\\tDuration: 170.24 ms\\tBilled Duration: 171 ms\\tMemory Size: 128 MB\\tMax Memory Used: 40 MB\\tInit Duration: 134.70 ms\\t\\n"'
        print(expected)
        assert response == expected

    def test_client_error(self, invoker):
        mock_error_response = {
            'Error': {
                'Message': 'Function not found: arn:aws:lambda:us-east-1:880306299867:function:function_not_found',
                'Code': 'ResourceNotFoundException'
            },
        }
        invoker.client.explore = mock.Mock()
        invoker.client.explore.side_effect = ClientError(
            operation_name="GetFunctionConfiguration",
            error_response=mock_error_response
        )

        with pytest.raises(ExplorationError) as error:
            invoker.invoke("wrong payload")
        assert error.type == ExplorationError

    @mock.patch("src.invocation.aws.aws_lambda_invoker.time.sleep")
    def test_max_number_of_invocations_attempts_reached_error(self, sleep, invoker):
        invoker.client.explore = mock.Mock(
            side_effect=(Exception() for _ in range(const.MAX_NUMBER_INVOCATION_ATTEMPTS)))

        with pytest.raises(ExplorationError) as error:
            invoker.invoke("payload")
        assert error.type == ExplorationError
        assert invoker.client.explore.call_count == const.MAX_NUMBER_INVOCATION_ATTEMPTS

    @mock.patch("src.invocation.aws.aws_lambda_invoker.time.sleep")
    def test_handling_aws_throttling(self, sleep, invoker):
        response = {"LogResult": "VGVzdCByZXNwb25zZQ=="}
        invoker.client.explore = mock.Mock(side_effect=(Exception(), Exception(), response))

        invoker.invoke("payload")

        assert invoker.client.explore.call_count == 3


class TestExecuteAndParseLogs:
    def test_max_number_invocation_error(self, invoker):
        invoker.invoke = mock.Mock(side_effect=ExplorationError("error"))

        with pytest.raises(ExplorationError) as e:
            invoker.explore("payload")
        assert e.type == ExplorationError

    def test_lambda_invocation_error(self, invoker):
        invoker.log_parser.parse_log = mock.Mock(side_effect=ExplorationError("error"))

        with pytest.raises(ExplorationError) as e:
            invoker.explore("payload")
        assert e.type == ExplorationError

    @pytest.mark.parametrize("error", [FunctionENOMEM(), FunctionENOMEM("lambda time out error")],
                             ids=["FunctionENOMEM", "FunctionTimeoutError"])
    def test_lambda_enomem(self, error, invoker):
        invoker.log_parser.parse_log = mock.Mock(side_effect=error)

        with pytest.raises(FunctionENOMEM) as e:
            invoker.explore("payload")
        assert e.type == FunctionENOMEM

    def test_read_time_out(self, invoker):
        # Arrange
        invoker.invoke = mock.Mock()
        invoker.invoke.side_effect = ReadTimeoutError(endpoint_url="endpoint"), \
            '\\tDuration: 18179.84 ms\\tBilled Duration: 18180.0 ms\\tMemory Size: 128 MB\\tMax Memory Used: 506.0 MB\\t\n'

        # Action
        invoker.explore("payload")

        # Assert
        assert invoker.invoke.call_count == 2


class TestCheckAndSetMemoryValue:
    def test_update_memory(self, invoker):
        config = invoker.check_and_set_memory_config(128)

        assert config["MemorySize"] == 128

    def test_param_value_error(self, invoker):
        invoker.client.update_function_configuration = mock.Mock(side_effect=ParamValidationError(report="error"))

        with pytest.raises(MemoryConfigError) as error:
            invoker.check_and_set_memory_config('wrong parm')
        assert error.type == MemoryConfigError

    def test_function_not_found(self, invoker):
        mock_error_response = {
            'Error': {
                'Message': 'Function not found: arn:aws:lambda:us-east-1:880306299867:function:function_not_found',
                'Code': 'ResourceNotFoundException'
            },
        }
        invoker.client.get_function_configuration = mock.Mock()
        invoker.client.get_function_configuration.side_effect = ClientError(
            operation_name="GetFunctionConfiguration",
            error_response=mock_error_response
        )

        with pytest.raises(MemoryConfigError) as error:
            invoker.check_and_set_memory_config(128)
        assert error.type == MemoryConfigError
