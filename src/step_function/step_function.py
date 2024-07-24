import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from jsonpath_ng import parse

from src.configuration import Configuration
from src.exception.step_function_error import StepFunctionError
from src.exploration.aws.aws_config_manager import AWSConfigManager
from src.logger import logger
from src.parrotfish import Parrotfish
from src.step_function.states import State, Task, Parallel, Map, Workflow


class StepFunction:
    def __init__(self, arn: str, input: str):
        self.function_tasks_dict = {}
        self.definition = self._load_definition(arn)
        self.workflow = self._create_workflow(self.definition)
        self._set_memory_for_all_functions()
        self._set_workflow_inputs(self.workflow, input)
        self._invoke_lambdas_in_parallel()
        pass

    def _load_definition(self, arn: str) -> dict:
        """Load a step function's definition."""
        try:
            response = boto3.client("stepfunctions").describe_state_machine(stateMachineArn=arn)
            definition = json.loads(response["definition"])
            return definition

        except Exception as e:
            logger.debug(e.args[0])
            raise StepFunctionError("Error loading definition.")

    def _create_workflow(self, workflow_def: dict) -> Workflow:
        """Create a Workflow object from a workflow definition."""

        def _create_state(name, state_def: dict) -> State:
            """Create a State object from a state definition."""
            if state_def["Type"] == "Task":
                function_name = state_def["Parameters"]["FunctionName"]
                task = Task(name, function_name)

                if function_name not in self.function_tasks_dict:
                    self.function_tasks_dict[function_name] = []
                self.function_tasks_dict[function_name].append(task)

                return task

            elif state_def["Type"] == "Parallel":
                parallel = Parallel(name)
                for branch_def in state_def["Branches"]:
                    branch = self._create_workflow(branch_def)
                    parallel.add_branch(branch)
                return parallel

            elif state_def["Type"] == "Map":
                map_state = Map(name)
                workflow = self._create_workflow(state_def["Iterator"])
                map_state.workflow = workflow
                map_state.items_path = state_def["ItemsPath"]
                return map_state

            else:
                raise StepFunctionError("Only Support Task, Parallel, Map State Types.")

        workflow = Workflow()
        state_name = workflow_def["StartAt"]  # starting state
        while 1:
            # add state to workflow
            state_def = workflow_def["States"][state_name]
            workflow.add_state(_create_state(state_name, state_def))

            # go to next state
            if "Next" in state_def:
                state_name = state_def["Next"]
            elif "End" in state_def:
                break  # end of workflow
            else:
                break  ## should throw an exception

        print("Workflow created.")
        return workflow

    def _set_memory_for_all_functions(self):
        """Set maximum memory size for all functions."""

        def set_memory_for_function(function_name):
            """Set memory size for one Lambda function"""
            aws_session = boto3.Session(region_name="ca-west-1")
            memory_size = 3008
            config_manager = AWSConfigManager(function_name, aws_session)
            config_manager.set_config(memory_size)

        error = None
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(set_memory_for_function, function_name)
                for function_name in self.function_tasks_dict
            ]

            for future in as_completed(futures):
                try:
                    config = future.result()
                    print("Set memory size completed, config: " + str(config))

                except Exception as e:
                    logger.debug(e)
                    if error is None:
                        error = e
                    continue

        if error:
            raise error

    def _set_workflow_inputs(self, workflow: Workflow, workflow_input: str) -> str:
        """Set inputs for the workflow states, chaining the output of each state to the input of the next."""

        def _extract_items(input_data: str, items_path: str) -> list[str]:
            """Extract a list of inputs from input JSON file"""
            matches = parse(items_path).find(json.loads(input_data))[0]
            return [json.dumps(item_dict) for item_dict in matches.value]

        def _set_state_input(state: State, input: str) -> str:
            if isinstance(state, Task):
                state.set_input(input)
                output = state.get_output()
                return output

            elif isinstance(state, Parallel):
                error = None

                outputs = []
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {
                        executor.submit(self._set_workflow_inputs, branch, input): branch
                        for branch in state.branches
                    }
                    for future in as_completed(futures):
                        branch = futures[future]
                        try:
                            branch_output = future.result()
                            outputs.append(branch_output)
                        except Exception as e:
                            logger.error(f"Error processing branch {branch}: {e}")
                            if error is None:
                                error = e
                            continue
                if error:
                    raise error
                return json.dumps(outputs)

            elif isinstance(state, Map):
                error = None
                inputs = _extract_items(input, state.items_path)
                state.iterations = [state.workflow for _ in range(len(inputs))]

                outputs = []
                with ThreadPoolExecutor(max_workers=10) as executor:
                    # Submit tasks for each iteration
                    futures = {
                        executor.submit(self._set_workflow_inputs, iteration, iteration_input): iteration_input
                        for iteration, iteration_input in zip(state.iterations, inputs)
                    }
                    for future in as_completed(futures):
                        iteration_input = futures[future]
                        try:
                            iteration_output = future.result()
                            outputs.append(iteration_output)
                        except Exception as e:
                            logger.error(f"Error processing iteration with input {iteration_input}: {e}")
                            if error is None:
                                error = e
                            continue
                if error:
                    raise error
                return json.dumps(outputs)

        payload = workflow_input
        for state in workflow.states:
            # The output of one function is the input of next function
            payload = _set_state_input(state, payload)
        return payload

    def _invoke_lambdas_in_parallel(self) -> list:
        def run_parrotfish(config):
            parrotfish = Parrotfish(Configuration(config))
            print("Optimize function: ", parrotfish.config.function_name)

            memory = parrotfish.optimize(apply=False)
            param_function = parrotfish.param_function

            print("Optimization finished: minimum memory= ", memory, ", function= ", parrotfish.config.function_name)
            return {"memory": memory, "param_function": param_function}

        error = None

        def run_function_with_inputs(tasks) -> list:
            results = []

            # run Parrotfish on each task
            for task in tasks:
                try:
                    config = {
                        "function_name": task.function_name,
                        "vendor": "AWS",
                        "region": "ca-west-1",
                        "payload": json.loads(task.input),
                        "termination_threshold": 2,
                        "min_sample_per_config": 3,
                        "dynamic_sampling_params": {
                            "max_sample_per_config": 3,
                            "coefficient_of_variation_threshold": 0.1
                        }
                    }
                    result = run_parrotfish(config)
                    results.append(result)
                except Exception as e:
                    logger.debug(e)
                    nonlocal error
                    if error is None:
                        error = e
                    continue

            return results

        with ThreadPoolExecutor(max_workers=10) as executor:
            # Run different functions in parallel
            futures = [executor.submit(run_function_with_inputs, tasks)
                       for tasks in self.function_tasks_dict.values()]

            results = []
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.debug(e)
                    if error is None:
                        error = e
                    continue

        if error:
            raise error

        return results
