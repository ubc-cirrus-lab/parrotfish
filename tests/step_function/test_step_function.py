from unittest.mock import MagicMock, Mock, patch

import pytest

from src.exploration.aws.aws_config_manager import AWSConfigManager
from src.step_function.states import Task, Parallel, Map, Workflow
from src.step_function.step_function import StepFunction


# from src.exploration.aws.aws_config_manager import AWSConfigManager


@pytest.fixture
def step_function():
    step_function = MagicMock(spec=StepFunction)
    step_function.config = Mock()
    step_function.function_tasks_dict = {}
    step_function.aws_session = Mock()

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

    def test_patch_interception(self):
        # Arrange: Simulate input parameters and setup
        function_name = "arn:aws:lambda:us-west-2:123456789:function:TestFunction"
        aws_session = MagicMock()

        with patch.object(AWSConfigManager, '__init__', return_value=None) as mock_init, \
                patch.object(AWSConfigManager, 'set_config', return_value=None) as mock_set_config:
            # Act: Create an instance of AWSConfigManager
            config_manager = AWSConfigManager(function_name, aws_session)

            # Assert: Check if the __init__ method was called with the correct arguments
            mock_init.assert_called_once_with(function_name, aws_session)

            # Act: Call the set_config method
            config_manager.set_config(3008)

            # Assert: Check if the set_config method was called with the correct argument
            mock_set_config.assert_called_once_with(3008)
