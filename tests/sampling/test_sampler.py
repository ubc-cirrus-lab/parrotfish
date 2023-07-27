from unittest import mock

import numpy as np
import pytest

from src.configuration import defaults
from src.exception import *
from src.sampling import *
from src.sampling.data_point import DataPoint
from tests.mocks import MockExplorer


@pytest.fixture
def sampler() -> Sampler:
    return Sampler(MockExplorer(), 3, defaults.DYNAMIC_SAMPLING_PARAMS)


class TestInitializeSample:
    def test_nominal_case(self, sampler):
        # Arrange
        def mock_update_sample(memory: int):
            sampler.sample.update(DataPoint(memory, 300))

        sampler.update_sample = mock_update_sample

        # Action
        sampler.initialize_sample()

        # Assert
        assert all(a == b for a, b in zip(sampler.sample.memories, [128, 1089, 3008]))
        assert all(a == b for a, b in zip(sampler.sample.durations, [300, 300, 300]))

    def test_function_enomem(self, sampler):
        # Arrange
        sampler.update_sample = mock.Mock(
            side_effect=(FunctionENOMEM, None, None, None)
        )

        # Action
        sampler.initialize_sample()

        # Assert
        assert sampler.memory_space[0] == 256
        assert sampler.update_sample.call_count == 4

    def test_sampling_error(self, sampler):
        sampler.update_sample = mock.Mock(side_effect=SamplingError("error"))

        with pytest.raises(SamplingError) as e:
            sampler.initialize_sample()
        assert e.type == SamplingError

    def test_no_memory_left_error(self, sampler):
        sampler.memory_space = [1, 2]

        with pytest.raises(NoMemoryLeftError) as e:
            sampler.initialize_sample()
        assert e.type == NoMemoryLeftError


class TestUpdateSample:
    def test_nominal_case(self, sampler):
        # Arrange
        sampler.sample = Sample()
        sampler.explorer.explore_parallel = mock.Mock(return_value=[300, 200, 400])
        sampler._explore_dynamically = mock.Mock(return_value=[300, 200, 400])

        # Action
        sampler.update_sample(128)

        # Assert
        assert all(a == b for a, b in zip(sampler.sample.durations, [300, 200, 400]))

    def test_sampling_error(self, sampler):
        sampler.explorer.explore_parallel = mock.Mock(
            side_effect=ExplorationError("error")
        )

        with pytest.raises(SamplingError) as e:
            sampler.update_sample(128)
        assert e.type == ExplorationError


class TestExploreDynamically:
    def test_nominal_case(self, sampler):
        # Arrange
        sampler.sample = Sample()
        sampler.explorer.explore = mock.Mock(side_effect=(110, 115, 120))

        # Action
        durations = sampler._explore_dynamically([10, 230, 1570])
        min_cv = np.std(durations, ddof=1) / np.mean(durations)

        # Assert
        assert sampler.explorer.explore.called
        assert min_cv < sampler._dynamic_sampling_params["coefficient_of_variation_threshold"]

    def test_sampling_error(self, sampler):
        sampler.explorer.explore = mock.Mock(side_effect=ExplorationError("error"))

        with pytest.raises(SamplingError) as e:
            sampler._explore_dynamically([10, 230, 1570])
        assert e.type == ExplorationError
