from unittest.mock import MagicMock

import pytest

from src.step_function.states import Parallel, Map, Workflow, Task


class TestStates:
    def test_parallel_state_add_branch(self):
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

    def test_map_state_set_workflow(self):
        # Arrange
        map_state = Map(name="test_map")
        workflow = Workflow()
        # Act
        map_state.add_iteration(workflow)
        # Assert
        assert len(map_state.iterations) == 1
        assert map_state.iterations[0] == workflow


@pytest.fixture
def mock_tasks():
    """Fixture to create mock tasks with predefined execution times."""
    task1 = Task(name="Task1", function_name="lambda_function_1")
    task1.get_execution_time = MagicMock(return_value=100)

    task2 = Task(name="Task2", function_name="lambda_function_1")
    task2.get_execution_time = MagicMock(return_value=150)

    task3 = Task(name="Task3", function_name="lambda_function_2")
    task3.get_execution_time = MagicMock(return_value=200)

    return task1, task2, task3


class TestCriticalPath:
    def test_get_critical_path_with_tasks(self, mock_tasks):
        # Arrange
        task1, task2, task3 = mock_tasks

        workflow = Workflow()
        workflow.add_state(task1)
        workflow.add_state(task2)
        workflow.add_state(task3)

        # Act
        critical_path, total_time = workflow.get_critical_path()

        # Assert
        assert critical_path == [task1, task2, task3]
        assert total_time == 450  # 100 + 150 + 200


    def test_get_critical_path_with_parallel_states(self, mock_tasks):
        # Arrange
        task1, task2, task3 = mock_tasks

        parallel_state = Parallel(name="Parallel1")
        parallel_state.add_branch(Workflow())
        parallel_state.branches[0].add_state(task1)
        parallel_state.branches[0].add_state(task2)

        parallel_state.add_branch(Workflow())
        parallel_state.branches[1].add_state(task3)

        workflow = Workflow()
        workflow.add_state(parallel_state)

        # Act
        critical_path, total_time = workflow.get_critical_path()

        # Assert
        assert critical_path == [task1, task2]
        assert total_time == 250  # 100 + 150


    def test_get_critical_path_with_map_states(self, mock_tasks):
        # Arrange
        task1, task2, task3 = mock_tasks

        map_state = Map(name="Map1")
        map_state.add_iteration(Workflow())
        map_state.iterations[0].add_state(task1)

        map_state.add_iteration(Workflow())
        map_state.iterations[1].add_state(task2)

        workflow = Workflow()
        workflow.add_state(map_state)

        # Act
        critical_path, total_time = workflow.get_critical_path()

        # Assert
        assert critical_path == [task2]
        assert total_time == 150


    def test_get_critical_path_with_mixed_states(self, mock_tasks):
        # Arrange
        task1, task2, task3 = mock_tasks

        parallel_state = Parallel(name="Parallel1")
        parallel_state.add_branch(Workflow())
        parallel_state.branches[0].add_state(task1)
        parallel_state.add_branch(Workflow())
        parallel_state.branches[1].add_state(task2)

        map_state = Map(name="Map1")
        map_state.add_iteration(Workflow())
        map_state.iterations[0].add_state(task3)

        workflow = Workflow()
        workflow.add_state(parallel_state)
        workflow.add_state(map_state)

        # Act
        critical_path, total_time = workflow.get_critical_path()

        # Assert
        assert critical_path == [task2, task3]
        assert total_time == 350  # 150 + 200
