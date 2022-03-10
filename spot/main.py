import time
import argparse
import os
from spot.definitions import ROOT_DIR
from spot.Spot import Spot

FUNCTION_DIR = "serverless_functions"


def main():
    parser = argparse.ArgumentParser(description="Serverless Price Optimization Tool")

    parser.add_argument(
        "function", type=str, help="Name of the serverless function to use"
    )
    parser.add_argument(
        "--invoke",
        "-i",
        action="store_true",
        help="Run the function with the given workload",
    )
    parser.add_argument(
        "--fetch", "-f", action="store_true", help="Fetch log and config data from AWS"
    )
    parser.add_argument(
        "--train",
        "-t",
        action="store_true",
        help="Train the model based on the fetched log and config data",
    )
    parser.add_argument(
        "--recommend",
        "-r",
        action="store_true",
        help="Recommend a memory config based on the trained model",
    )
    parser.add_argument(
        "--profile",
        "-p",
        action="store_true",
        help="Test multiple memory configs to determine the optimal one",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="linear",
        help="The ML model to use to train the model (default: linear)",
    )

    args = parser.parse_args()

    if args.function is not None:
        path = os.path.join(ROOT_DIR, FUNCTION_DIR, args.function)
        if os.path.isdir(path):
            function = Spot(path, args.model)
            if args.invoke:
                function.invoke()
            if args.fetch:
                if args.invoke:
                    time.sleep(15)  # TODO: Change this to waiting all threads to yield
                function.collect_data()
            if args.train:
                function.train_model()
            if args.recommend:
                pass  # TODO: Recommend something if flag is set
            if args.profile:
                pass  # TODO: Run multiple configurations if flag is set
        else:
            print(
                f"Could not find the serverless function {args.function} in '{path}'. Functions are case sensitive"
            )
    else:
        print(f"Please specify a serverless function from the {FUNCTION_DIR} directory")


if __name__ == "__main__":
    main()
