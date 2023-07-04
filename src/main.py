import argparse
import logging.config
import os

import boto3

from src.constants import ROOT_DIR
from src.exceptions import OptimizationError
from src.spot import Spot

FUNCTION_DIR = "configs"

logging.config.dictConfig({"version": 1, "disable_existing_loggers": True})
logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


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
        print(
            f"Could not find the serverless function {args.function} in '{path}'. Functions are case sensitive"
        )
        exit(1)

    spot = Spot(path, session)

    if args.optimize:
        try:
            result = spot.optimize()
        except OptimizationError as e:
            logger.critical(e)
            exit(1)
        else:
            logger.info(result)
            opt_memory_mb = result["Minimum Cost Memory"]
            print(f"Optimization result: {opt_memory_mb} MB")
            args.memory_mb = int(opt_memory_mb)

    if args.invoke:
        if not args.memory_mb:
            print("Please specify a memory value when invoking a function")
            exit(1)
        spot.invoke(args.memory_mb, args.invoke)


if __name__ == "__main__":
    main()
