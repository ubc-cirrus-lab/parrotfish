import argparse
import logging
import os

from src.configuration import Configuration
from src.exception import OptimizationError
from src.logging import logger
from src.parrotfish import Parrotfish


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Parametric Regression for Optimizing Serverless Functions"
    )

    parser.add_argument("--path", "-p", type=str, help="Path to the configuration file")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Set the logging level to INFO"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply optimized configuration"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(level=logging.INFO)

    # Retrieve configuration for the file
    config_file_path = os.path.join(os.getcwd(), "parrotfish.json")
    if args.path:
        config_file_path = args.path

    try:
        with open(config_file_path) as config_file:
            configuration = Configuration(config_file)

    except ValueError as e:
        logger.critical(e.args[0])
        exit(1)

    except FileNotFoundError:
        logger.critical(f"No configuration file is found in {config_file_path}")
        exit(1)

    parrotfish = Parrotfish(configuration)

    try:
        result = parrotfish.optimize()

    except OptimizationError as e:
        logger.critical(e)
        exit(1)

    else:
        logger.info(result)
        opt_memory_mb = result["Minimum Cost Memory"]
        print(f"Optimization result: {opt_memory_mb} MB")
        if args.apply:
            parrotfish.configure(opt_memory_mb)
