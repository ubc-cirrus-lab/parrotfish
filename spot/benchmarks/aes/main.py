from spot.benchmarks.base_benchmark import BaseBenchmark


class executeAes(BaseBenchmark):
    def __init__(self, config="config.json"):
        super().__init__(__file__, config=config)
        self.run()
