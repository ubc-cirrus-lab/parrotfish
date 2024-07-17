import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from jsonpath_ng import parse

from src.exception.step_function_error import StepFunctionError
from src.logger import logger
from src.step_function.states import State, Task, Parallel, Map, Workflow


class StepFunction:
    def __init__(self, arn: str, input: str):
        self.input = input
        self.definition = self._load_definition(arn)
        self.workflow, _ = self._create_workflow(self.definition, self.input)
        pass

    def _load_definition(self, arn: str) -> dict:
        """Load a step function's definition."""
        try:
            response = boto3.client("stepfunctions").describe_state_machine(
                stateMachineArn=arn
            )
            definition = json.loads(response["definition"])
            return definition

        except Exception as e:
            logger.debug(e.args[0])
            raise StepFunctionError("Error loading definition.")

    def _create_workflow(self, workflow_def: dict, workflow_input: str) -> tuple[Workflow, str]:
        """Create a Workflow object from the workflow definition and input."""
        try:
            workflow = Workflow()

            state_name = workflow_def["StartAt"]  # starting state
            payload = workflow_input
            while True:
                state_def = workflow_def["States"][state_name]
                # output payload is the input payload for next state
                [state, payload] = self._create_state(state_name, state_def, payload)
                # add state to workflow
                workflow.add_state(state)

                # go to next state
                if "Next" in state_def:
                    state_name = state_def["Next"]
                else:
                    break  # end of workflow

            return workflow, payload

        except Exception as e:
            logger.debug(e.args[0])
            raise StepFunctionError("Error creating workflow")

    def _create_state(self, name, state_def: dict, input: str) -> tuple[State, str]:
        """Create a State object from the state definition and input."""

        if state_def["Type"] == "Task":
            function_name = state_def["Parameters"]["FunctionName"]
            task = Task(name, function_name)
            task.set_input(input)
            output = task.get_output()
            return task, output

        elif state_def["Type"] == "Parallel":
            parallel = Parallel(name)
            outputs = []
            futures = []

            # Create branches in parallel
            with ThreadPoolExecutor() as executor:
                for branch_def in state_def["Branches"]:
                    futures.append(executor.submit(self._create_workflow, branch_def, input))

                for future in as_completed(futures):
                    branch, branch_output = future.result()
                    parallel.add_branch(branch)
                    outputs.append(branch_output)

            output = json.dumps(outputs)
            return parallel, output

        elif state_def["Type"] == "Map":
            # Extract a list of inputs from input JSON file
            def _extract_items(input_data: str, items_path: str) -> list[str]:
                matches = parse(items_path).find(json.loads(input_data))[0]
                return [json.dumps(item_dict) for item_dict in matches.value]

            map = Map(name)
            outputs = []
            futures = []
            iteration_def = state_def["Iterator"]
            inputs = _extract_items(input, state_def["ItemsPath"])

            # Create iterations in parallel
            with ThreadPoolExecutor() as executor:
                for item_input in inputs:
                    futures.append(
                        executor.submit(self._create_workflow, iteration_def, item_input)
                    )

                for future in as_completed(futures):
                    iteration, iteration_output = future.result()
                    map.set_workflow(iteration)
                    outputs.append(iteration_output)

            output = json.dumps(outputs)
            return map, output


        else:
            raise StepFunctionError(
                "State definition only support Task, Parallel and Map type states.")
