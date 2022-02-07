from spot.Spot import Spot

def executeChromeScreenshot():
    file_path = "spot/benchmarks/ChromeScreenshot/config.json"
    benchmark = Spot(file_path)
    benchmark.execute()
