import numpy as np
import pytest

from spot.data_model import *


@pytest.fixture
def initial_params():
    return [1000, 10000, 100]


@pytest.fixture
def fitting_function(initial_params):
    # Define a test function
    def fn(x, a, b, c):
        return a * x + b * np.exp(-x / c) * x

    bounds = ([0, 0, 0], [np.inf, np.inf, np.inf])

    # Create an instance of FittingFunction with the test function and initial parameters
    return FittingFunction(function=fn, params=initial_params, bounds=bounds)


def test_fit_function(initial_params, fitting_function):
    # Generate some test data.
    memories = np.array([128, 256, 512, 1024])
    billed_time = np.array([30, 20, 10, 6])
    datapoints = [DataPoint(memory=mem, billed_time=time) for mem, time in zip(memories, billed_time)]

    # Fitting the function.
    fitting_function.fit(datapoints)

    # Test number of parameters is the same.
    assert len(fitting_function.params) == len(initial_params)

    # Test if function's parameters updated.
    for param, initial_param in zip(fitting_function.params, initial_params):
        assert param != initial_param


def test_fit_function_raise_value_error(fitting_function):
    # If datapoints contains invalid values.
    memories = np.array([np.NaN, 256, 512, 1024])
    billed_time = np.array([30, 20, 10, 6])
    datapoints = [DataPoint(memory=mem, billed_time=time) for mem, time in zip(memories, billed_time)]

    # Test that the fit_function raises a ValueError
    with pytest.raises(ValueError) as e:
        fitting_function.fit(datapoints)

    assert e.type == ValueError
