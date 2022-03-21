import time
import argparse
import os
from spot.constants import ROOT_DIR
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
        help="The ML model to use to train the model (default: linear)",
    )
    parser.add_argument(
        "--update_config",
        "-u",
        action="store_true",
        help="Update lambda function config with the optimal config current model suggests",
    )
    parser.add_argument(
        "--plot_error_vs_epoch",
        "-ee",
        action="store_true",
        help="Plot error vs epoch",
    )
    parser.add_argument(
        "--plot_config_vs_epoch",
        "-ce",
        action="store_true",
        help="Plot config vs epoch",
    )
    parser.add_argument(
        "--plot_memsize_vs_cost",
        "-mc",
        action="store_true",
        help="Plot Memory Size vs Cost",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="End-to-end execution of full lifecycle: profiling then fetching newly created logs, then training the model, then recommending the optimal config and updating the serverless function config with the new config",
    )

    args = parser.parse_args()

    if args.full:
        """
        End-to-end execution of full lifecycle: 
            1. profiling
            2. fetching newly created logs
            3. training the model 
            4. recommending the optimal config 
            5. updating the serverless function config with the new config
        """
        args.profile = args.fetch = args.train = args.update_config = True

    if args.function is not None:
        path = os.path.join(ROOT_DIR, FUNCTION_DIR, args.function)
        if os.path.isdir(path):
            function = Spot(path, args.model)
            if args.invoke:
                function.invoke()
            if args.profile:
                function.profile()
            if args.fetch:
                if args.invoke:
                    time.sleep(15)  # TODO: Change this to waiting all threads to yield
                function.collect_data()
            if args.train:
                if args.model:
                    function.train_model()
                else:
                    print("Please specify model")
                    return
            if args.recommend:
                if args.model:
                    function.recommend()
                else:
                    print("Please specify model")
                    return
            if args.update_config:
                if args.model:
                    function.update_config()
                    function.get_prediction_error_rate()
                else:
                    print("Please specify model")
                    return
            if args.plot_error_vs_epoch:
                function.plot_error_vs_epoch()
            if args.plot_config_vs_epoch:
                function.plot_config_vs_epoch()
            if args.plot_memsize_vs_cost:
                if (args.train or args.full) and args.model:
                    function.plot_memsize_vs_cost()
                else:
                    print("Memsize vs Cost plot can be generated only after training")
                    return
        else:
            print(
                f"Could not find the serverless function {args.function} in '{path}'. Functions are case sensitive"
            )
    else:
        print(f"Please specify a serverless function from the {FUNCTION_DIR} directory")


if __name__ == "__main__":
    main()
