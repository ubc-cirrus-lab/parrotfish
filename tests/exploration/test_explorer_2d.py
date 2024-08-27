import concurrent.futures
from unittest import mock
import pytest
from src.exception import *
from tests.mocks import MockExplorer2D

class TestExploreParallel2D:
    @pytest.fixture
    def explorer(self):
        return MockExplorer2D()

    @mock.patch("src.exploration.explorer_2d.as_completed")
    @mock.patch("src.exploration.explorer_2d.ThreadPoolExecutor")
    def test_parallel_execution(self, executor, as_completed, explorer):
        # Arrange
        class MockFuture(concurrent.futures.Future):
            def __init__(self, result):
                super().__init__()
                self._result = result

            def result(self, timeout=None):
                return self._result

        executor.return_value.submit = lambda _, payload: None
        as_completed.return_value = [MockFuture(300), MockFuture(400), MockFuture(200)]
        explorer.check_and_set_memory_config = mock.Mock()
        explorer.price_calculator.calculate_price = mock.Mock(return_value=10)
        expected = [300, 400, 200]

        # Action
        results = explorer.explore_parallel(3, 3)

        # Assert
        explorer.check_and_set_memory_config.assert_not_called()
        assert results == expected
        assert explorer.cost == 0  # Cost calculation commented out in the code

    @pytest.mark.parametrize(
        "error",
        [InvocationError("error", 300), FunctionENOMEM(duration_ms=300)],
        ids=["InvocationError", "FunctionENOMEM"],
    )
    @mock.patch("src.exploration.explorer_2d.as_completed")
    @mock.patch("src.exploration.explorer_2d.ThreadPoolExecutor")
    def test_invocation_error(self, executor, as_completed, error, explorer):
        # Arrange
        class MockFuture(concurrent.futures.Future):
            def __init__(self, result):
                super().__init__()
                self._result = result

            def result(self, timeout=None):
                raise error

        executor.return_value.submit = lambda _, payload: None
        as_completed.return_value = [MockFuture(300)]
        explorer.price_calculator.calculate_price = mock.Mock(return_value=10)

        # Action and Assert
        with pytest.raises(ExplorationError) as e:
            explorer.explore_parallel(3, 3)
        assert e.value == error
        assert explorer.cost == 0  # Cost calculation commented out in the code


class TestExplore2D:
    @pytest.fixture
    def explorer(self):
        explorer = MockExplorer2D()
        explorer.check_and_set_memory_config = mock.Mock()
        explorer.invoke = mock.Mock()
        explorer.handle_cold_start = mock.Mock()
        explorer.price_calculator.calculate_price = mock.Mock(return_value=10)
        return explorer

    def test_nominal_case(self, explorer):
        duration_ms = explorer.explore(enable_cost_calculation = True)

        assert explorer.price_calculator.calculate_price.called
        assert explorer.cost == 10
        assert duration_ms == 18180

    def test_memory_and_cpu_config_changed(self, explorer):
        explorer.explore(memory_mb=128, cpu=0.5)

        assert explorer.config_manager.set_config.called

    def test_function_config_error(self, explorer):
        explorer.config_manager.set_config = mock.Mock(
            side_effect=FunctionConfigError("error")
        )

        with pytest.raises(ExplorationError) as e:
            explorer.explore(memory_mb=128, cpu=0.5)
        assert e.type == FunctionConfigError

    def test_invocation_error_raised_by_invoke(self, explorer):
        explorer.invoker.invoke = mock.Mock(side_effect=InvocationError("error", 120))

        with pytest.raises(ExplorationError) as e:
            explorer.explore()
        assert e.type == InvocationError

    def test_compute_cost_raises_cost_calculation_error(self, explorer):
        explorer.price_calculator.calculate_price = mock.Mock(
            side_effect=CostCalculationError("error")
        )

        with pytest.raises(ExplorationError) as e:
            explorer.explore(enable_cost_calculation=True)
        assert e.type == CostCalculationError
