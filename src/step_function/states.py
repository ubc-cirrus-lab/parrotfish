from abc import ABC, abstractmethod

import boto3

from src.exploration.aws.aws_invoker import AWSInvoker


class State(ABC):
    """Base class for Task and Parallel states."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_execution_time(self) -> float:
        pass


class Task(State):
    """Task state in Step Function."""

    def __init__(self, name: str, function_name: str):
        super().__init__(name)
        self.function_name = function_name

    def set_input(self, input: str):
        self.input = input

    def get_output(self) -> str:
        aws_session = boto3.Session(region_name="ca-west-1")
        #
        # # Set memory size of the function to maximum
        # memory_size = 3008
        # config_manager = AWSConfigManager(self.function_name, aws_session)
        # config_manager.set_config(memory_size)
        # print("Memory size: " + str(memory_size) + "MB")

        # Invoke function to get output
        print("Start invocation, function_name: " + self.function_name + " , input: " + self.input)
        invoker = AWSInvoker(
            function_name=self.function_name,
            max_invocation_attempts=5,
            aws_session=aws_session,
        )
        output = invoker.invoke_for_output(self.input)
        print("Finish invocation, function_name: " + self.function_name + " , input: " + self.input)
        return output

    def get_execution_time(self) -> float:
        return 1


class Parallel(State):
    """Parallel state, holding multiple parallel workflows."""

    def __init__(self, name: str):
        super().__init__(name)
        self.branches: list[Workflow] = []

    def add_branch(self, workflow: "Workflow"):
        self.branches.append(workflow)

    def get_execution_time(self) -> float:
        """Returns the longest execution time among all branches."""
        max_time = 0
        for branch in self.branches:
            branch_time = branch.get_execution_time()
            max_time = max(max_time, branch_time)
        return max_time


class Map(State):
    """Map state, holding a single workflow to be iterated."""

    def __init__(self, name: str):
        super().__init__(name)
        self.iterations: list[Workflow] = []
        self.workflow = None
        self.items_path = ""

    def set_workflow(self, workflow: "Workflow"):
        self.iterations.append(workflow)

    def get_execution_time(self) -> float:
        """Returns the longest execution time among all branches."""
        max_time = 0
        for branch in self.iterations:
            branch_time = branch.get_execution_time()
            max_time = max(max_time, branch_time)
        return max_time


class Workflow:
    """A workflow, containing a sequence of states."""

    def __init__(self):
        self.states: list[State] = []

    def add_state(self, state: State):
        self.states.append(state)

    def get_execution_time(self) -> float:
        total_time = sum(state.get_execution_time() for state in self.states)
        return total_time
