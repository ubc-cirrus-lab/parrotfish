import time
import boto3
import argparse
import os
from spot.constants import ROOT_DIR
from spot.Spot import Spot

FUNCTION_DIR = "configs"


def main():
    parser = argparse.ArgumentParser(description="Serverless Price Optimization Tool")

    parser.add_argument(
        "function", type=str, help="Name of the serverless function to use"
    )
    parser.add_argument(
        "--optimize",
        "-o",
        action="store_true",
        help="Return best memory configuration for lowest cost",
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="Ignore the invocation cache"
    )
    parser.add_argument(
        "--invoke", "-i", type=int, help="The number of times you invoke the function"
    )
    parser.add_argument(
        "--memory_mb", "-m", type=int, help="Memory (MB) of the function"
    )
    parser.add_argument("--aws_profile", "-p", type=str, help="AWS profile")

    args = parser.parse_args()

    if args.aws_profile:
        session = boto3.Session(profile_name=args.aws_profile)
    else:
        session = boto3.Session()

    if not args.function:
        print(f"Please specify a serverless function from the {FUNCTION_DIR} directory")
        exit(1)

    path = os.path.join(ROOT_DIR, "../", FUNCTION_DIR, args.function)
    if not os.path.isdir(path):
        print(f"Could not find the serverless function {args.function} in '{path}'. Functions are case sensitive")
        exit(1)

    start = time.time()
    spot = Spot(path, session)
    optimization_time = None
    if args.optimize:
        opt = spot.optimize()
        mem = opt["Minimum Cost Memory"][0]
        print(f"Optimization result: {mem} MB")
        args.memory_mb = int(mem)
        optimization_time = time.time() - start
    if args.invoke:
        if not args.memory_mb:
            print("Please specify a memory value when invoking a function")
            exit(1)
        spot.invoke(args.memory_mb, args.invoke, args.force)

    spot.teardown(optimization_time)


if __name__ == "__main__":
    main()
