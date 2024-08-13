from abc import ABC

import boto3

from src.exploration.aws.aws_invoker import AWSInvoker
from src.logger import logger


class State(ABC):
    """Base class for Task, Parallel and Map states."""

    def __init__(self, name: str):
        self.name = name


class Task(State):
    """Task: a single Lambda function """

    def __init__(self, name: str, function_name: str):
        super().__init__(name)
        self.function_name = function_name
        self.parrotfish = None

    def set_input(self, input: str):
        self.input = input

    def get_output(self, aws_session: boto3.Session) -> str:
        logger.debug(f"Invoking {self.function_name}, input: {self.input}")

        invoker = AWSInvoker(
            function_name=self.function_name,
            max_invocation_attempts=5,
            aws_session=aws_session,
        )
        output = invoker.invoke_for_output(self.input)

        logger.debug(f"Finish invoking {self.function_name}, output: {output}")
        return output


class Parallel(State):
    """Parallel: parallel workflows (branches) with same input."""

    def __init__(self, name: str):
        super().__init__(name)
        self.branches: list[Workflow] = []

    def add_branch(self, workflow: "Workflow"):
        self.branches.append(workflow)


class Map(State):
    """Map: multiple same workflows with different inputs"""

    def __init__(self, name: str):
        super().__init__(name)
        self.iterations: list[Workflow] = []
        self.workflow = None
        self.items_path = ""

    def add_iteration(self, workflow: "Workflow"):
        self.iterations.append(workflow)


class Workflow:
    """A workflow, containing a sequence of states."""

    def __init__(self):
        self.states: list[State] = []

    def add_state(self, state: State):
        self.states.append(state)
