import matplotlib.pyplot as plt

from src.data_model import Sample
from src.recommendation import ParametricFunction
from src.recommendation.reporter import Reporter


class Profiler(Reporter):
    def __init__(self, param_function: ParametricFunction, sample: Sample):
        super().__init__(param_function)
        self.sample = sample

    def report(self):
        plt.plot(self.sample.memories, self.param_function(self.sample.memories) / 1000)
<<<<<<< HEAD
        plt.plot(self.sample.memories, self.param_function(self.sample.memories) / self.sample.memories)
        plt.xlabel('Memory size in MB')
        plt.ylabel('Cost is USD, Execution time in ms')
        plt.savefig('figure.png')
=======
        plt.plot(
            self.sample.memories,
            self.param_function(self.sample.memories) / self.sample.memories,
        )
        plt.xlabel("Memory size in MB")
        plt.ylabel("Cost is USD, Execution time in ms")
        plt.savefig("figure.png")
>>>>>>> ebc6e044602b0c7e50d8c7b6d0613a5a873fc0fc
