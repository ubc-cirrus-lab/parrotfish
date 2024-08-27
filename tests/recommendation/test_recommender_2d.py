from unittest import mock

import numpy as np
import pytest

from src.exception import *
from src.recommendation import Recommender2D
from src.sampling import Sample2D
from src.sampling.data_point_2d import DataPoint2D

@pytest.fixture
def recommender_2d():
    objective_2d = mock.Mock()
    sampler_2d = mock.Mock()
    return Recommender2D(objective_2d, sampler_2d, 5)

class TestInitialize:
    def test_nominal_case(self, recommender_2d):
        # Arrange
        def mock_initialize_sample():
            recommender_2d.sampler.sample = Sample2D(
                [
                    DataPoint2D(0.08, 128, 280), 
                    DataPoint2D(0.08, 128, 300), 
                    DataPoint2D(0.08, 128, 270),
                    DataPoint2D(0.08, 128, 260), 
                    DataPoint2D(0.08, 128, 290),
                ]
            )

        recommender_2d.sampler.initialize_sample = mock_initialize_sample
        recommender_2d.objective.update_knowledge = mock.Mock()
        recommender_2d.objective.cpu_mem_duration_function.fit = mock.Mock()

        # Action
        recommender_2d._initialize()

        # Assert
        assert recommender_2d.objective.update_knowledge.called
        assert recommender_2d.objective.cpu_mem_duration_function.fit.called

    def test_fitting_error(self, recommender_2d):
        # Arrange
        def mock_initialize_sample():
            recommender_2d.sampler.sample = Sample2D(
                [
                    DataPoint2D(0.08, 128, 280), 
                    DataPoint2D(0.08, 128, 300), 
                    DataPoint2D(0.08, 128, 270),
                    DataPoint2D(0.08, 128, 260), 
                    DataPoint2D(0.08, 128, 290),
                ]
            )

        recommender_2d.sampler.initialize_sample = mock_initialize_sample
        recommender_2d.objective.update_knowledge = mock.Mock()
        recommender_2d.objective.cpu_mem_duration_function.fit = mock.Mock(
            side_effect=RuntimeError({})
        )

        # Action
        with pytest.raises(OptimizationError) as e:
            recommender_2d._initialize()

        # Assert
        assert e.type == OptimizationError
        assert recommender_2d.objective.update_knowledge.called

class TestUpdate:
    def test_nominal_case(self, recommender_2d):
        # Arrange
        recommender_2d.sampler.update_sample = mock.Mock()
        recommender_2d.objective.update_knowledge = mock.Mock()
        recommender_2d.objective.cpu_mem_duration_function.fit = mock.Mock()

        # Action
        recommender_2d._update(0.08, 128)

        # Assert
        assert recommender_2d.sampler.update_sample.called
        assert recommender_2d.objective.update_knowledge.called
        assert recommender_2d.objective.cpu_mem_duration_function.fit.called

    def test_fitting_error(self, recommender_2d):
        # Arrange
        recommender_2d.sampler.update_sample = mock.Mock()
        recommender_2d.objective.update_knowledge = mock.Mock()
        recommender_2d.objective.cpu_mem_duration_function.fit = mock.Mock(
            side_effect=RuntimeError({})
        )

        # Action
        with pytest.raises(OptimizationError) as e:
            recommender_2d._update(0.08, 128)
        
        # Assert
        assert e.type == OptimizationError
        assert recommender_2d.sampler.update_sample.called
        assert recommender_2d.objective.update_knowledge.called

class TestChooseCpuMemoryToExplore:
    def test_nominal_cases(self, recommender_2d):
        # Arrange
        recommender_2d.sampler.sample = Sample2D(
            [
                DataPoint2D(0.08, 128, 280), 
                DataPoint2D(0.08, 128, 300), 
                DataPoint2D(0.08, 128, 270),
                DataPoint2D(0.08, 128, 260), 
                DataPoint2D(0.08, 128, 290),
            ]
        )
        recommender_2d.sampler.cpu_mem_space = [
            [0.08, 128],
            [0.08, 256]
        ]
        recommender_2d.objective.get_values = mock.Mock(return_value=np.array([1.6]))

        # Action
        [cpu, mem] = recommender_2d._choose_cpu_memory_to_explore()

        # Assert
        assert cpu == 0.08
        assert mem == 256

    def test_no_cpu_memory_left_error(self, recommender_2d):
        # Arrange
        recommender_2d.sampler.sample = Sample2D(
            [
                DataPoint2D(0.08, 128, 280), 
                DataPoint2D(0.08, 128, 300), 
                DataPoint2D(0.08, 128, 270),
                DataPoint2D(0.08, 128, 260), 
                DataPoint2D(0.08, 128, 290),
            ]
        )
        recommender_2d.sampler.cpu_mem_space = [
            [0.08, 128]
        ]

        # Action
        with pytest.raises(NoMemoryLeftError) as e:
            recommender_2d._choose_cpu_memory_to_explore()
        assert e.type == NoMemoryLeftError
