from abc import ABC, abstractmethod

import boto3


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
        lambda_client = boto3.client("lambda", region_name="ca-west-1")
        print("Start invocation, function_name: " + self.function_name + " , input: " + self.input)
        response = lambda_client.invoke(
            FunctionName=self.function_name,
            InvocationType='RequestResponse',
            Payload=self.input
        )
        print("Finish invocation, function_name: " + self.function_name + " , input: " + self.input)
        output = response['Payload'].read().decode('utf-8')
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
