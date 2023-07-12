import argparse
import logging.config

from src.configuration import Configuration
from src.exceptions import OptimizationError
from src.parrotfish import Parrotfish

logging.config.dictConfig({"version": 1, "disable_existing_loggers": True})
logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Parametric Regression for Optimizing Serverless Functions")
    parser.add_argument("config_file_path", type=str, help="Name of the serverless function to use")
    parser.add_argument(
        "--optimize",
        "-o",
        action="store_true",
        help="Return best memory configuration for lowest cost",
    )
    parser.add_argument("--invoke", "-i", type=int, help="The number of times you invoke the function")
    args = parser.parse_args()

    # Load configuration values from config.json
    if not args.config_file_path:
        args.config_file_path = "config.json"
    try:
        with open(args.config_file_path) as config_file:
            config: Configuration = Configuration(config_file)
    except FileNotFoundError as e:
        print(e.args[0])

    parrotfish = Parrotfish(config)

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
            args.memory_mb = int(opt_memory_mb)

    if args.invoke:
        if not args.memory_mb:
            print("Please specify a memory value when invoking a function")
            exit(1)
        parrotfish.invoke(args.memory_mb, args.invoke)


if __name__ == "__main__":
    main()
