import numpy as np
import pytest

from src.objective import CpuMemDurationFunction
from src.sampling import Sample2D
from src.sampling.data_point_2d import DataPoint2D

@pytest.fixture
def cpu_mem_duration_function():
    return CpuMemDurationFunction()

class TestFittingFunction:
    def test_fit_function(self, cpu_mem_duration_function):
        # Generate some test data.
        cpus = np.array([0.08, 0.21, 0.34, 0.47, 0.61])
        memories = np.array([128, 256, 512, 1024, 2048])
        durations = np.array([300, 250, 200, 100, 50])
        sample = Sample2D(
            [
                DataPoint2D(cpu, mem, duration)
                for cpu, mem, duration in zip(cpus, memories, durations)
            ]
        )

        # Fitting the function.
        cpu_mem_duration_function.fit(sample)

        # Test if function's parameters updated.
        assert cpu_mem_duration_function.params is not None

    def test_fit_function_raise_value_error(self, cpu_mem_duration_function):
        # If datapoints contain invalid values.
        cpus = np.array([np.NaN, 0.21, 0.34, 0.47, 0.61])
        memories = np.array([128, 256, np.NaN, 1024, 2048])
        durations = np.array([300, 250, 200, np.NaN, 50])
        sample = Sample2D(
            [
                DataPoint2D(cpu, mem, duration)
                for cpu, mem, duration in zip(cpus, memories, durations)
            ]
        )

        # Test that the fit_function raises a ValueError
        with pytest.raises(ValueError) as e:
            cpu_mem_duration_function.fit(sample)

        assert e.type == ValueError