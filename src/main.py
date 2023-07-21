import argparse
import logging.config
import os

from src.configuration import Configuration
from src.exceptions import OptimizationError
from src.parrotfish import Parrotfish

logging.config.dictConfig({"version": 1, "disable_existing_loggers": True})
logging.basicConfig(
    format="%(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Serverless Price Optimization Tool")

    parser.add_argument("--path", "-p", type=str, help="Path to the configuration file")
    parser.add_argument(
        "--optimize",
        "-o",
        action="store_true",
        help="Return best memory configuration for lowest cost",
    )
    parser.add_argument(
        "--memory_mb", "-m", type=int, help="Memory (MB) of the function"
    )
    parser.add_argument(
        "--invoke", "-i", type=int, help="The number of times you invoke the function"
    )

    args = parser.parse_args()

    config_file_path = os.path.join(os.getcwd(), "parrotfish.json")
    if args.path:
        config_file_path = args.path

    with open(config_file_path) as config_file:
        configuration = Configuration(config_file)

    parrotfish = Parrotfish(configuration)

    if args.optimize:
        try:
            result = parrotfish.optimize()
        except OptimizationError as e:
            logger.critical(e)
            exit(1)
        else:
            logger.info(result)
            opt_memory_mb = result["Minimum Cost Memory"]
            print(f"Optimization result: {opt_memory_mb} MB")

    if args.invoke:
        if not args.memory_mb:
            logger.critical("Please specify a memory value when invoking a function")
            exit(1)
        parrotfish.invoke(args.memory_mb, args.invoke)


if __name__ == "__main__":
    main()
