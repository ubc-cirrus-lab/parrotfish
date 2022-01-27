from spot.Spot import Spot

def executeAWSHelloWorld():
    file_path = "spot/benchmarks/AWSHelloWorld/config.json"
    benchmark = Spot(file_path)
    benchmark.execute()