from unittest import mock

import boto3
import pytest

from src.exploration.aws.aws_invoker import AWSInvoker
from src.step_function.states import Task, Parallel, Map, Workflow


@pytest.fixture
def aws_session():
    return boto3.Session(region_name="us-west-2")


def test_task_state_invoke(aws_session):
    # Arrange
    task_state = Task(name="test_task", function_name="test_lambda")
    task_state.set_input("input_data")
    mock_invoker = mock.Mock(spec=AWSInvoker)
    mock_invoker.invoke_for_output.return_value = "output_data"
    # Act
    output = task_state.get_output(aws_session)
    # Assert
    assert output == "output_data"


def test_parallel_state_add_branch(aws_session):
    # Arrange
    parallel_state = Parallel(name="test_parallel")
    workflow1 = Workflow()
    workflow2 = Workflow()
    # Act
    parallel_state.add_branch(workflow1)
    parallel_state.add_branch(workflow2)
    # Assert
    assert len(parallel_state.branches) == 2
    assert parallel_state.branches[0] == workflow1
    assert parallel_state.branches[1] == workflow2


def test_map_state_set_workflow(aws_session):
    # Arrange
    map_state = Map(name="test_map")
    workflow = Workflow()
    # Act
    map_state.add_iteration(workflow)
    # Assert
    assert len(map_state.iterations) == 1
    assert map_state.iterations[0] == workflow
