from abc import ABC, abstractmethod
from typing import Tuple

import boto3

from src.exploration.aws.aws_invoker import AWSInvoker
from src.logger import logger


class State(ABC):
    """Base class for Task, Parallel and Map states."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_cost(self) -> float:
        pass


class Task(State):
    """Task: a single Lambda function """

    def __init__(self, name: str, function_name: str):
        super().__init__(name)
        self.function_name = function_name
        self.input = None
        self.param_function = None
        self.memory_size = None

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

    def increase_memory_size(self, increment: int):
        self.memory_size += increment

    def decrease_memory_size(self, decrement: int):
        self.memory_size -= decrement

    def get_execution_time(self, memory_size: int = None):
        if memory_size is not None:
            execution_time = self.param_function(memory_size)
        else:
            execution_time = self.param_function(self.memory_size)
        return execution_time

    def get_cost(self, memory_size: int = None):
        if memory_size is not None:
            execution_time = memory_size * self.param_function(memory_size)
        else:
            execution_time = self.memory_size * self.param_function(self.memory_size)
        return execution_time


class Parallel(State):
    """Parallel: parallel workflows (branches) with same input."""

    def __init__(self, name: str):
        super().__init__(name)
        self.branches: list[Workflow] = []

    def add_branch(self, workflow: "Workflow"):
        self.branches.append(workflow)

    def get_critical_path(self) -> Tuple[list[Task], float]:
        """Get tasks on critical path and execution time."""
        max_time = 0.0
        critical_path = None
        for workflow in self.branches:
            states, time = workflow.get_critical_path()
            if time > max_time:
                max_time = time
                critical_path = states
        return critical_path, max_time

    def get_cost(self) -> float:
        return sum(workflow.get_cost() for workflow in self.branches)


class Map(State):
    """Map: multiple same workflows with different inputs."""

    def __init__(self, name: str):
        super().__init__(name)
        self.items_path = None
        self.workflow_def = None
        self.iterations: list[Workflow] = []

    def add_iteration(self, workflow: "Workflow"):
        self.iterations.append(workflow)

    def get_critical_path(self) -> Tuple[list[Task], float]:
        max_time = 0.0
        critical_path = None
        for workflow in self.iterations:
            states, time = workflow.get_critical_path()
            if time > max_time:
                max_time = time
                critical_path = states
        return critical_path, max_time

    def get_cost(self) -> float:
        return sum(workflow.get_cost() for workflow in self.iterations)


class Workflow:
    """A workflow, containing a sequence of states."""

    def __init__(self):
        self.states: list[State] = []

    def add_state(self, state: State):
        self.states.append(state)

    def get_critical_path(self) -> Tuple[list[Task], float]:
        critical_path: list[Task] = []
        total_time = 0.0

        for state in self.states:
            if isinstance(state, Task):
                critical_path.append(state)
                time = state.get_execution_time()
                total_time += time
            elif isinstance(state, (Parallel, Map)):
                states, time = state.get_critical_path()
                critical_path.extend(states)
                total_time += time

        return critical_path, total_time

    def get_cost(self) -> float:
        return sum(state.get_cost() for state in self.states)
