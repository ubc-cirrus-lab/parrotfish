import logging.config

from src.configuration import defaults

logging.config.dictConfig({"version": 1, "disable_existing_loggers": True})
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=defaults.LOG_LEVEL
)
logger = logging.getLogger("main")
