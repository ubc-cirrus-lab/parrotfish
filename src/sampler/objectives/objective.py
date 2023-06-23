from abc import ABC, abstractmethod
from spot.data_model import *


class Objective(ABC):
    # memory range is a list [min, max], objective function is the function we want to minimize in order to determine
    # the next sample.
    def __init__(self, fitting_function: FittingFunction, memory_range: list):
        self.fitting_function = fitting_function
        self.memory_range = memory_range

    @abstractmethod
    def get_value(self, x):
        pass

    @abstractmethod
    def update_knowledge(self, x):
        pass

    @abstractmethod
    def get_knowledge(self, x):
        pass
