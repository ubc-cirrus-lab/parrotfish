from spot.benchmarks.base_benchmark import BaseBenchmark


class AWSHelloWorldBenchmark(BaseBenchmark):
    def __init__(self):
        super().__init__(__file__)
        self.run()

