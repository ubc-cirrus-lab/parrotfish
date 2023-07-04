from unittest import mock

import numpy as np
import pytest

from src.data_model import *
from src.exceptions import *
from src.recommendation import Recommender


@pytest.fixture
def recommender():
    objective = mock.Mock()
    sampler = mock.Mock()
    return Recommender(objective, sampler, 3, 1.5)


class TestInitialize:
    def test_nominal_case(self, recommender):
        # Arrange
        def mock_initialize_sample():
            recommender.sampler.sample = Sample(
                [DataPoint(128, 200), DataPoint(128, 300), DataPoint(128, 400)]
            )

        recommender.sampler.initialize_sample = mock_initialize_sample
        recommender.objective.update_knowledge = mock.Mock()
        recommender.objective.param_function.fit = mock.Mock()

        # Action
        recommender._initialize()

        # Assert
        assert recommender.objective.update_knowledge.called
        assert recommender.objective.param_function.fit.called

    def test_fitting_error(self, recommender):
        # Arrange
        def mock_initialize_sample():
            recommender.sampler.sample = Sample(
                [DataPoint(128, 200), DataPoint(128, 300), DataPoint(128, 400)]
            )

        recommender.sampler.initialize_sample = mock_initialize_sample
        recommender.objective.update_knowledge = mock.Mock()
        recommender.objective.param_function.fit = mock.Mock(
            side_effect=RuntimeError({})
        )

        with pytest.raises(OptimizationError) as e:
            recommender._initialize()
        assert e.type == OptimizationError
        assert recommender.objective.update_knowledge.called


class TestUpdate:
    def test_nominal_case(self, recommender):
        # Arrange
        recommender.sampler.update_sample = mock.Mock()
        recommender.objective.update_knowledge = mock.Mock()
        recommender.objective.param_function.fit = mock.Mock()

        # Action
        recommender._update(128)

        # Assert
        assert recommender.sampler.update_sample.called
        assert recommender.objective.update_knowledge.called
        assert recommender.objective.param_function.fit.called

    def test_fitting_error(self, recommender):
        recommender.sampler.update_sample = mock.Mock()
        recommender.objective.update_knowledge = mock.Mock()
        recommender.objective.param_function.fit = mock.Mock(
            side_effect=RuntimeError({})
        )

        with pytest.raises(OptimizationError) as e:
            recommender._update(128)
        assert e.type == OptimizationError
        assert recommender.sampler.update_sample.called
        assert recommender.objective.update_knowledge.called


class TestChooseMemoryToExplore:
    def test_nominal_case(self, recommender):
        # Arrange
        recommender.sampler.sample = Sample(
            [DataPoint(128, 200), DataPoint(128, 300), DataPoint(128, 400)]
        )
        recommender.sampler.memory_space = [128, 256]
        recommender.objective.get_values = mock.Mock(return_value=np.array([1.6]))

        # Action
        mem = recommender._choose_memory_to_explore()

        # Assert
        assert mem == 256

    def test_no_memory_left_error(self, recommender):
        recommender.sampler.sample = Sample(
            [DataPoint(128, 200), DataPoint(128, 300), DataPoint(128, 400)]
        )
        recommender.sampler.memory_space = [128]

        with pytest.raises(NoMemoryLeftError) as e:
            recommender._choose_memory_to_explore()
        assert e.type == NoMemoryLeftError
