import numpy as np
import pytest

from src.recommendation import *
from src.data_model import *


@pytest.fixture
def param_function():
    bounds = ([0, 0, 0], [np.inf, np.inf, np.inf])
    return ParametricFunction(
        function=lambda x, a, b, c: a * x + b * np.exp(-x / c) * x, bounds=bounds
    )


class TestFittingFunction:
    def test_fit_function(self, param_function):
        # Generate some test data.
        memories = np.array([128, 256, 512, 1024])
        billed_time = np.array([30, 20, 10, 6])
        sample = Sample(
            [
                DataPoint(memory_mb=mem, duration_ms=time)
                for mem, time in zip(memories, billed_time)
            ]
        )

        # Fitting the function.
        param_function.fit(sample)

        # Test if function's parameters updated.
        assert param_function.params is not None

    def test_fit_function_raise_value_error(self, param_function):
        # If datapoints contains invalid values.
        memories = np.array([np.NaN, 256, 512, 1024])
        billed_time = np.array([30, 20, 10, 6])
        sample = Sample(
            [
                DataPoint(memory_mb=mem, duration_ms=time)
                for mem, time in zip(memories, billed_time)
            ]
        )

        # Test that the fit_function raises a ValueError
        with pytest.raises(ValueError) as e:
            param_function.fit(sample)

        assert e.type == ValueError
