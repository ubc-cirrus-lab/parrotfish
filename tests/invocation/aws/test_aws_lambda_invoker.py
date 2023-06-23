import concurrent.futures
import pandas as pd
import pytest
from unittest import mock
from botocore.exceptions import *

import src.constants as const
from src.invocation.aws import AWSLambdaInvoker
from src.exceptions import *


@pytest.fixture
def invoker():
    client = mock.Mock()

    client.invoke.return_value = {
        "LogResult": "IkR1cmF0aW9uIjogMTgxNzkuODQsICJCaWxsZWQgRHVyYXRpb24iOiAxODE4MC4wLCAiTWF4IE1lbW9yeSBVc2VkIjogNTA2L"
                     "jAsICJNZW1vcnkgU2l6ZSI6IDUxMi4w"
    }

    client.get_function_configuration.return_value = {"MemorySize": 256, "LastUpdateStatus": "Successful"}

    def mock_update_function_configuration(FunctionName: str, MemorySize: int):
        client.get_function_configuration.side_effect = (
            {"MemorySize": MemorySize, "LastUpdateStatus": "InProgress"},
            {"MemorySize": MemorySize, "LastUpdateStatus": "Successful"},
        )

    client.update_function_configuration = mock_update_function_configuration

    return AWSLambdaInvoker("example_function", client)


class TestInvoke:
    class MockFuture(concurrent.futures.Future):
        def __init__(self, result):
            super().__init__()
            self._result = result

        def result(self, timeout=None):
            return self._result

    def test_function_memory_config_error(self, invoker):
        invoker.check_and_set_memory_value = mock.Mock(side_effect=FunctionMemoryConfigError("error"))

        with pytest.raises(FunctionMemoryConfigError) as e:
            invoker.invoke(3, 3, 128, "payload")
        assert e.type == FunctionMemoryConfigError

    def test_function_invocation_error(self, invoker):
        invoker.check_and_set_memory_value = mock.Mock()
        invoker._execute_and_parse_logs = mock.Mock(side_effect=InvocationError("error"))

        with pytest.raises(InvocationError) as e:
            invoker.invoke(3, 3, 128, "payload")
        assert e.type == InvocationError

    def test_lambda_enomem(self, invoker):
        invoker.check_and_set_memory_value = mock.Mock()
        invoker._execute_and_parse_logs = mock.Mock(side_effect=FunctionENOMEM)

        with pytest.raises(FunctionENOMEM) as e:
            invoker.invoke(3, 3, 128, "payload")
        assert e.type == FunctionENOMEM

    @mock.patch("src.invocation.function_invoker.as_completed")
    @mock.patch("src.invocation.function_invoker.ThreadPoolExecutor")
    def test_parallel_execution(self, executor, as_completed, invoker):
        invoker.check_and_set_memory_value = mock.Mock()
        def mock_submit(_, payload):
            pass
        executor.return_value.submit = mock_submit
        as_completed.return_value = [
            self.MockFuture({"Duration": 300, "Billed Duration": 300, "Max Memory Used": 100, "Memory Size": 128}),
            self.MockFuture({"Duration": 400, "Billed Duration": 400, "Max Memory Used": 90, "Memory Size": 128}),
            self.MockFuture({"Duration": 200, "Billed Duration": 200, "Max Memory Used": 120, "Memory Size": 128})
        ]
        expected = pd.DataFrame.from_dict({
            "Duration": [300, 400, 200],
            "Billed Duration": [300, 400, 200],
            "Max Memory Used": [100, 90, 120],
            "Memory Size": [128, 128, 128]
        })

        results = invoker.invoke(3, 3, 128, "payload")

        assert results.equals(expected)


class TestExecuteFunction:
    def test_nominal_case(self, invoker):
        response = invoker.execute_function("payload")
        expected_response = 'b\'"Duration": 18179.84, "Billed Duration": 18180.0, "Max Memory Used": 506.0, "Memory ' \
                            'Size": 512.0\''

        assert response == expected_response

    def test_client_error(self, invoker):
        mock_error_response = {
            'Error': {
                'Message': 'Function not found: arn:aws:lambda:us-east-1:880306299867:function:function_not_found',
                'Code': 'ResourceNotFoundException'
            },
        }
        invoker.client.invoke = mock.Mock()
        invoker.client.invoke.side_effect = ClientError(
            operation_name="GetFunctionConfiguration",
            error_response=mock_error_response
        )

        with pytest.raises(InvocationError) as error:
            invoker.execute_function("wrong payload")
        assert error.type == InvocationError

    @mock.patch("src.invocation.aws.aws_lambda_invoker.time.sleep")
    def test_max_number_of_invocations_attempts_reached_error(self, sleep, invoker):
        invoker.client.invoke = mock.Mock(
            side_effect=(Exception() for _ in range(const.MAX_NUMBER_INVOCATION_ATTEMPTS)))

        with pytest.raises(InvocationError) as error:
            invoker.execute_function("payload")
        assert error.type == InvocationError
        assert invoker.client.invoke.call_count == const.MAX_NUMBER_INVOCATION_ATTEMPTS

    @mock.patch("src.invocation.aws.aws_lambda_invoker.time.sleep")
    def test_handling_aws_throttling(self, sleep, invoker):
        response = {"LogResult": "VGVzdCByZXNwb25zZQ=="}
        invoker.client.invoke = mock.Mock(side_effect=(Exception(), Exception(), response))

        invoker.execute_function("payload")

        assert invoker.client.invoke.call_count == 3


class TestExecuteAndParseLogs:
    def test_max_number_invocation_error(self, invoker):
        invoker.execute_function = mock.Mock(side_effect=InvocationError("error"))

        with pytest.raises(InvocationError) as e:
            invoker._execute_and_parse_logs("payload")
        assert e.type == InvocationError

    def test_single_invocation_error(self, invoker):
        invoker.log_parser.parse_log = mock.Mock(side_effect=InvocationError("error"))

        with pytest.raises(InvocationError) as e:
            invoker._execute_and_parse_logs("payload")
        assert e.type == InvocationError

    @pytest.mark.parametrize("error", [FunctionENOMEM(), FunctionTimeoutError()],
                             ids=["FunctionENOMEM", "FunctionTimeoutError"])
    def test_lambda_enomem(self, error, invoker):
        invoker.log_parser.parse_log = mock.Mock(side_effect=error)

        with pytest.raises(FunctionENOMEM) as e:
            invoker._execute_and_parse_logs("payload")
        assert e.type == FunctionENOMEM

    def test_read_time_out(self, invoker):
        invoker.log_parser.parse_log = mock.Mock()
        invoker.log_parser.parse_log.side_effect = ReadTimeoutError(endpoint_url="endpoint"), \
            {"Duration": 18179.84, "Billed Duration": 18180.0, "Max Memory Used": 506.0, "Memory Size": 512.0}

        invoker._execute_and_parse_logs("payload")

        assert invoker.log_parser.parse_log.call_count == 2


class TestCheckAndSetMemoryValue:
    def test_update_memory(self, invoker):
        config = invoker.check_and_set_memory_value(128)

        assert config["MemorySize"] == 128

    def test_param_value_error(self, invoker):
        invoker.client.update_function_configuration = mock.Mock(side_effect=ParamValidationError(report="error"))

        with pytest.raises(FunctionMemoryConfigError) as error:
            invoker.check_and_set_memory_value('wrong parm')
        assert error.type == FunctionMemoryConfigError

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

        with pytest.raises(FunctionMemoryConfigError) as error:
            invoker.check_and_set_memory_value(128)
        assert error.type == FunctionMemoryConfigError
