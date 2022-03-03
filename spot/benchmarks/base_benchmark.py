from spot.Spot import Spot
from spot.definitions import ROOT_DIR
import os


class BaseBenchmark:
    def __init__(self, file_name: str, config="config.json"):
        self.file_path = os.path.join(ROOT_DIR, os.path.dirname(file_name))
        self.config_path = os.path.join(self.file_path, config)

    def run(self):
        benchmark = Spot(self.config_path)
        benchmark.execute()

    def sample_invocation(self):
        raise NotImplementedError
