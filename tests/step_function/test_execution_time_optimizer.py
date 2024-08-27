import pytest
from unittest.mock import MagicMock

from src.step_function.execution_time_optimizer import ExecutionTimeOptimizer


class TestInitializeCostIncreases:
    @pytest.fixture
    def optimizer(self):
        workflow = MagicMock()
        config = MagicMock(memory_size_increment=128)

        function_tasks_dict = {
            'func1': [MagicMock(memory_size=128, get_cost=MagicMock(side_effect=lambda mem_size: 0.02 if mem_size == 128 else 0.025))],
            'func2': [MagicMock(memory_size=256, get_cost=MagicMock(side_effect=lambda mem_size: 0.04 if mem_size == 256 else 0.05))]
        }

        optimizer = ExecutionTimeOptimizer(workflow, function_tasks_dict, config)
        return optimizer

    def test_initialize_cost_increases(self, optimizer):
        # Action
        cost_increases = optimizer._initialize_cost_increases()

        # Assert
        assert cost_increases == {'func1': 0.025 - 0.02, 'func2': 0.05 - 0.04}


class TestCalculateTimeReductions:
    @pytest.fixture
    def optimizer(self):
        workflow = MagicMock()
        config = MagicMock(memory_size_increment=128)

        task1 = MagicMock()
        task1.function_name = 'function1'
        task1.memory_size = 128
        task1.max_memory_size = 256
        task1.get_execution_time.side_effect = [100, 80]

        task2 = MagicMock()
        task2.function_name = 'function2'
        task2.memory_size = 256
        task2.max_memory_size = 512
        task2.get_execution_time.side_effect = [200, 150]

        optimizer = ExecutionTimeOptimizer(workflow, {}, config)
        return optimizer, [task1, task2]

    def test_calculate_time_reductions(self, optimizer):
        # Arrange
        optimizer_instance, critical_path_tasks = optimizer

        # Action
        time_reductions = optimizer_instance._calculate_time_reductions(critical_path_tasks)

        # Assert
        assert time_reductions['function1'] == 20
        assert time_reductions['function2'] == 50


class TestFindBestFunctionToOptimize:
    @pytest.fixture
    def optimizer(self):
        workflow = MagicMock()
        config = MagicMock(memory_size_increment=128)
        function_tasks_dict = MagicMock(memory_size_increment=128)

        optimizer = ExecutionTimeOptimizer(workflow, function_tasks_dict, config)
        return optimizer

    def test_find_best_function_to_optimize(self, optimizer):
        # Arrange
        cost_increases = {'func1': 5, 'func2': 1}
        time_reductions = {'func1': 20, 'func2': 50}

        # Action
        best_function = optimizer._find_best_function_to_optimize(cost_increases, time_reductions)

        # Assert
        assert best_function == 'func2' # 5 / 20 > 1 / 50

class TestUpdateMemorySizeAndCost:
    @pytest.fixture
    def optimizer(self):
        workflow = MagicMock()
        config = MagicMock(memory_size_increment=128)

        task1 = MagicMock()
        task1.memory_size = 128
        task1.get_cost.side_effect = [0.02, 0.025]
        task1.increase_memory_size = MagicMock()

        function_tasks_dict = {'func1': [task1]}

        optimizer = ExecutionTimeOptimizer(workflow, function_tasks_dict, config)
        return optimizer, task1

    def test_update_memory_size_and_cost(self, optimizer):
        # Arrange
        optimizer_instance, task1 = optimizer
        cost_increases = {'func1': 0.0}

        # Action
        optimizer_instance._update_memory_size_and_cost('func1', cost_increases)

        # Assert
        task1.increase_memory_size.assert_called_once_with(128)  # Check memory increment
        assert cost_increases['func1'] == 0.025 - 0.02

