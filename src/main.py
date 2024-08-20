import argparse
import logging
import os

from src.configuration import Configuration
from src.configuration.step_function_configuration import StepFunctionConfiguration
from src.exception import OptimizationError
from src.logger import logger
from src.parrotfish import Parrotfish
from src.step_function.step_function import StepFunction


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
    parser.add_argument(
        "--step-function", action="store_true", help="Optimize a step function"
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
            if args.step_function:
                configuration = StepFunctionConfiguration(config_file)
            else:
                configuration = Configuration(config_file)

    except ValueError as e:
        logger.critical(e.args[0])
        exit(1)

    except FileNotFoundError:
        logger.critical(f"No configuration file is found in {config_file_path}")
        exit(1)

    if args.step_function:
        # Create step function
        step_function = StepFunction(configuration)

        # Run Parrotfish and execution time optimization to get cost optimized memories
        step_function.optimize()

    else:
        parrotfish = Parrotfish(configuration)

        try:
            parrotfish.optimize(args.apply)

        except OptimizationError as e:
            logger.critical(e)
            exit(1)
