from unittest import mock
import pytest
from requests.exceptions import HTTPError
from google.api_core.exceptions import GoogleAPICallError
from src.exception import InvocationError, MaxInvocationAttemptsReachedError
from src.exploration.gcp.gcp_invoker_v2 import GCPInvokerV2
from src.configuration import defaults


@pytest.fixture
@mock.patch("src.exploration.gcp.gcp_invoker_v2.functions_v2")
@mock.patch("src.exploration.gcp.gcp_invoker_v2.google_logging")
def invoker(functions_v2, google_logging):
    credentials = type("", (), {})()
    credentials.project_id = "example_project_id"
    credentials.region = "example_region"
    functions_v2.FunctionServiceClient = mock.Mock()
    google_logging.Client = mock.Mock()
    return GCPInvokerV2(
        function_name="example_function",
        credentials=credentials,
        max_invocation_attempts=defaults.MAX_NUMBER_OF_INVOCATION_ATTEMPTS,
    )


class TestInvokeV2:
    @mock.patch("src.exploration.gcp.gcp_invoker_v2.requests.post")
    def test_nominal_case(self, mock_post, invoker):
        # Arrange
        mock_response = mock.Mock()
        mock_response.json.return_value = {'response': 1.234}
        mock_response.raise_for_status = mock.Mock()
        mock_post.return_value = mock_response
        expected_result = 1234

        # Action
        response = invoker.invoke(payload='{"key": "value"}')

        # Assert
        assert response == expected_result
        mock_post.assert_called_once_with(
            invoker.function_url, json={"key": "value"}
        )

    @mock.patch("src.exploration.gcp.gcp_invoker_v2.requests.post")
    def test_calling_error(self, mock_post, invoker):
        mock_post.side_effect = GoogleAPICallError("error")

        with pytest.raises(InvocationError) as e:
            invoker.invoke(payload='{"key": "value"}')

        assert e.type == InvocationError

    @mock.patch("src.exploration.gcp.gcp_invoker_v2.requests.post")
    def test_http_error(self, mock_post, invoker):
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = HTTPError("HTTP Error")
        mock_post.return_value = mock_response

        with pytest.raises(MaxInvocationAttemptsReachedError) as e:
            invoker.invoke(payload='{"key": "value"}')

        assert e.type == MaxInvocationAttemptsReachedError

    @mock.patch("src.exploration.gcp.gcp_invoker_v2.time.sleep")
    @mock.patch("src.exploration.gcp.gcp_invoker_v2.requests.post")
    def test_max_number_of_invocations_attempts_reached_error(self, mock_post, mock_sleep, invoker):
        mock_post.side_effect = Exception("Too Many Requests")

        with pytest.raises(MaxInvocationAttemptsReachedError) as error:
            invoker.invoke(payload='{"key": "value"}')

        assert error.type == MaxInvocationAttemptsReachedError
        assert mock_post.call_count == defaults.MAX_NUMBER_OF_INVOCATION_ATTEMPTS
