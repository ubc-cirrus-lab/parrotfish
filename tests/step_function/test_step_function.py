from unittest.mock import MagicMock, Mock, patch

import pytest

from src.exception.step_function_error import StepFunctionError
from src.exploration.aws.aws_config_manager import AWSConfigManager
from src.step_function.states import Task, Parallel, Map, Workflow
from src.step_function.step_function import StepFunction


@pytest.fixture
def step_function():
    step_function = MagicMock(spec=StepFunction)
    step_function.config = Mock()
    step_function.function_tasks_dict = {}
    step_function.aws_session = Mock()
    step_function.workflow = MagicMock()

    step_function._load_definition = StepFunction._load_definition.__get__(step_function, StepFunction)
    return step_function


class TestStepFunction:
    def test_load_definition_direct_initialization(self, step_function):
        # Arrange
        step_function.aws_session.client().describe_state_machine.return_value = {
            'definition': '{"StartAt":"GetInput","States":{"GetInput":{"Type":"Task","Resource":"arn:aws:states:::lambda:invoke","OutputPath":"$.Payload","Parameters":{"Payload.$":"$","FunctionName":"arn:aws:lambda:us-west-2:898429789601:function:ImageProcessingGetInput"},"Retry":[{"ErrorEquals":["Lambda.ServiceException","Lambda.AWSLambdaException","Lambda.SdkClientException"],"IntervalSeconds":2,"MaxAttempts":6,"BackoffRate":2}],"End":true}}}'
        }

        # Act
        definition = step_function._load_definition("test_arn")

        # Assertion
        assert (definition["States"] ==
                {'GetInput': {'Type': 'Task', 'Resource': 'arn:aws:states:::lambda:invoke', 'OutputPath': '$.Payload',
                              'Parameters': {'Payload.$': '$',
                                             'FunctionName': 'arn:aws:lambda:us-west-2:898429789601:function:ImageProcessingGetInput'},
                              'Retry': [{'ErrorEquals': ['Lambda.ServiceException', 'Lambda.AWSLambdaException',
                                                         'Lambda.SdkClientException'], 'IntervalSeconds': 2,
                                         'MaxAttempts': 6, 'BackoffRate': 2}], 'End': True}})

    @patch.object(AWSConfigManager, '__init__', return_value=None)
    @patch.object(AWSConfigManager, 'set_config', return_value=None)
    def test_create_workflow_task_state(self, mock_config_manager, step_function):
        # Arrange
        workflow_def = {
            "StartAt": "Task",
            "States": {
                "Task": {
                    "Type": "Task",
                    "Parameters": {
                        "FunctionName": "TaskFunction"
                    },
                    "Next": "Map"
                },
                "Map": {
                    "Type": "Map",
                    "Iterator": {
                        "States": {
                            "Image Recognition": {
                                "Type": "Task",
                                "Parameters": {
                                    "FunctionName": "MapFunction"
                                }
                            }
                        }
                    },
                    "ItemsPath": "$.body.data.filenames",
                    "Next": "Parallel"
                },
                "Parallel": {
                    "Type": "Parallel",
                    "Branches": [
                        {
                            "States": {
                                "FirstModel": {
                                    "Type": "Task",
                                    "Parameters": {
                                        "FunctionName": "ParallelFunction1"
                                    }
                                }
                            }
                        },
                        {
                            "States": {
                                "SecondModel": {
                                    "Type": "Task",
                                    "Parameters": {
                                        "FunctionName": "ParallelFunction2"
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }

        # Act
        workflow = StepFunction._create_workflow(step_function, workflow_def)

        # Assert
        assert isinstance(workflow, Workflow)
        assert len(workflow.states) == 3
        assert isinstance(workflow.states[0], Task)
        assert workflow.states[0].function_name == "TaskFunction"
        assert isinstance(workflow.states[1], Map)
        assert isinstance(workflow.states[2], Parallel)
        assert len(workflow.states[2].branches) == 2

class TestExecutionTimeConstraintOptimization:
    def create_step_function(self):
        step_function = StepFunction()  # Replace with your actual class
        step_function.config = MagicMock()
        step_function.workflow = MagicMock()
        step_function.function_tasks_dict = {}
        step_function.config.memory_size_increment = 128
        return step_function

    def create_mock_task(self, memory_size, max_memory_size, execution_time, cost):
        """Helper function to create a mock task with specified properties."""
        task = MagicMock()
        task.memory_size = memory_size
        task.max_memory_size = max_memory_size
        task.get_execution_time = MagicMock(return_value=execution_time)
        task.get_cost = MagicMock(side_effect=lambda memory: cost)
        task.function_name = 'function1'
        return task

    def test_threshold_high(self):
        # Arrange
        step_function = self.create_step_function()
        step_function.config.constraint_execution_time_threshold = 300
        task = self.create_mock_task(128, 512, 250, 0.01)
        step_function.function_tasks_dict = {'function1': [task]}
        step_function.workflow.get_critical_path = MagicMock(return_value=([task], 250))

        # Action
        step_function._optimize_for_execution_time_constraint()

        # Assert
        task.increase_memory_size.assert_not_called()

    def test_threshold_low(self):
        # Arrange
        step_function = self.create_step_function()
        step_function.config.constraint_execution_time_threshold = 50
        task = self.create_mock_task(128, 512, 250, 0.01)
        step_function.function_tasks_dict = {'function1': [task]}

        # Action
        step_function.workflow.get_critical_path = MagicMock(return_value=([task], 250))

        # Assert
        with pytest.raises(StepFunctionError) as e:
            step_function._optimize_for_execution_time_constraint()
        assert e.type == StepFunctionError

