from unittest import mock

import pytest

from src.configuration import defaults
from src.exception import *
from src.sampling import Sampler2D, Sample2D
from src.sampling.data_point_2d import DataPoint2D
from tests.mocks import MockExplorer2D


@pytest.fixture
def sampler_2d() -> Sampler2D:
    return Sampler2D(MockExplorer2D(), 5, defaults.DYNAMIC_SAMPLING_PARAMS)


class TestInitializeSample:
    def test_nominal_case(self, sampler_2d):
        # Arrange
        def mock_update_sample(cpu: float, memory: int):
            sampler_2d.sample.update(DataPoint2D(cpu, memory, 300))

        sampler_2d.update_sample = mock_update_sample

        # Action
        sampler_2d.initialize_sample()

        # Assert
        assert all(a[0] == b[0] and a[1] == b[1] for a, b in zip(sampler_2d.sample.cpu_mems, [[0.08, 128], [0.08, 512], [0.21, 896],[0.21, 1280],[0.21, 1664]]))
        assert all(a == b for a, b in zip(sampler_2d.sample.durations, [0.3, 0.3, 0.3, 0.3, 0.3]))

    def test_sampling_error(self, sampler_2d):
        sampler_2d.update_sample = mock.Mock(side_effect=SamplingError("error"))

        with pytest.raises(SamplingError) as e:
            sampler_2d.initialize_sample()
        assert e.type == SamplingError

    def test_no_memory_left_error(self, sampler_2d):
        sampler_2d.cpu_mem_space = [[0.08, 1], [0.08, 2]]

        with pytest.raises(NoMemoryLeftError) as e:
            sampler_2d.initialize_sample()
        assert e.type == NoMemoryLeftError


class TestUpdateSample:
    def test_nominal_case(self, sampler_2d):
        # Arrange
        sampler_2d.sample = Sample2D()
        sampler_2d.explorer.explore_parallel = mock.Mock(return_value=[300, 200, 400, 100, 500])
        sampler_2d._explore_dynamically = mock.Mock(return_value=[300, 200, 400, 100, 500])

        # Action
        sampler_2d.update_sample(0.08, 128)

        # Assert
        assert all(a == b for a, b in zip(sampler_2d.sample.durations, [0.3, 0.2, 0.4, 0.1, 0.5]))

    def test_sampling_error(self, sampler_2d):
        sampler_2d.explorer.explore_parallel = mock.Mock(
            side_effect=ExplorationError("error")
        )

        with pytest.raises(SamplingError) as e:
            sampler_2d.update_sample(0.08, 128)
        assert e.type == ExplorationError


class TestExploreDynamically:

    def test_sampling_error(self, sampler_2d):
        sampler_2d.explorer.explore = mock.Mock(side_effect=ExplorationError("error"))

        with pytest.raises(SamplingError) as e:
            sampler_2d._explore_dynamically([10, 230, 1570, 19820, 230458])
        assert e.type == ExplorationError
