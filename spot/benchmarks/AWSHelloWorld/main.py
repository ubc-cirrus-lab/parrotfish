from spot.benchmarks.base_benchmark import BaseBenchmark


class executeAWSHelloWorld(BaseBenchmark):
    def __init__(self):
        super().__init__(__file__)
        self.run()

