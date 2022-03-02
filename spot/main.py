from getopt import getopt, error
import sys
from spot.benchmarks.AWSHelloWorld.main import executeAWSHelloWorld
from spot.benchmarks.formplug.main import executeFormplug
from spot.benchmarks.ChromeScreenshot.main import executeChromeScreenshot
from spot.benchmarks.aes.main import executeAes

# List of benchmarks and associated functions. Note: The key should be all lower case!
benchmarks = {
    "awshelloworld": executeAWSHelloWorld,
    "formplug": executeFormplug,
    "chromescreenshot": executeChromeScreenshot,
    "aes": executeAes,
}


def main():
    arguments = sys.argv[1:]
    options = "hb:c:"
    long_options = ["Help", "Benchmark", "Config"]

    try:
        args_vals, _ = getopt(arguments, options, long_options)
        benchmark = None
        config_file = "config_new.json"

        for arg, val in args_vals:
            print(f"{arg}, {val}")
            if arg in ("-h", "--Help"):
                print("Sorry, cannot help you. 🇨🇦")

            if arg in ("-b", "--Benchmark"):
                print(val)
                if val.lower() in benchmarks:
                    print(f"Running benchmark: {val}")
                    benchmark = benchmarks[val.lower()]

            if arg in ("-c", "--Config"):
                config_file = val.strip()
        
        if benchmark is not None:
            benchmark(config=config_file)

    except error as err:
        print(str(err))


if __name__ == "__main__":
    main()
