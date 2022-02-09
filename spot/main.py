from getopt import getopt, error
import sys
from spot.benchmarks.AWSHelloWorld.main import executeAWSHelloWorld
from spot.benchmarks.formplug.main import executeFormplug
from spot.benchmarks.ChromeScreenshot.main import executeChromeScreenshot

# List of benchmarks and associated functions. Note: The key should be all lower case!
benchmarks = {
    "awshelloworld": executeAWSHelloWorld,
    "formplug": executeFormplug,
    "chromescreenshot": executeChromeScreenshot,
}


def main():
    arguments = sys.argv[1:]
    options = "hb:"
    long_options = ["Help", "Benchmark"]

    try:
        args_vals, _ = getopt(arguments, options, long_options)

        for arg, val in args_vals:

            if arg in ("-h", "--Help"):
                print("Sorry, cannot help you. 🇨🇦")

            if arg in ("-b", "--Benchmark"):
                print(val)
                if val.lower() in benchmarks:
                    print(f"Running benchmark: {val}")
                    benchmarks[val.lower()]()
    except error as err:
        print(str(err))
    
if __name__ == '__main__':
    main()
