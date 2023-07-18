import matplotlib.pyplot as plt

from src.data_model import Sample
from src.recommendation import ParametricFunction
from src.recommendation.reporter import Reporter


class Visualizer(Reporter):
    def __init__(self, param_function: ParametricFunction, sample: Sample):
        super().__init__(param_function)
        self.sample = sample

    def report(self):
        plt.plot(self.sample.memories, self.param_function(self.sample.memories) / 1000)
        plt.plot(
            self.sample.memories,
            self.param_function(self.sample.memories) / self.sample.memories,
        )
        plt.xlabel("Memory size in MB")
        plt.ylabel("Cost is USD, Execution time in ms")
        plt.savefig("figure.png")
        return 'figure.png'
