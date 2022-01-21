from spot.Spot import Spot

def executeHelloWorld():
    file_path = "spot/benchmarks/HelloWorld/config.json"
    benchmark = Spot(file_path)
    benchmark.execute()