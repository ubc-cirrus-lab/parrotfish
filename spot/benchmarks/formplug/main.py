from spot.Spot import Spot
import os


def executeFormplug():
    # os.getcwd()
    file_path = os.path.join(os.path.dirname(__file__), "config.json")
    benchmark = Spot(file_path)
    benchmark.execute()