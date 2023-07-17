from abc import ABC, abstractmethod

from src.recommendation import ParametricFunction


class Reporter(ABC):
    def __init__(self, param_function: ParametricFunction):
        self.param_function = param_function

    @abstractmethod
    def report(self):
        pass
