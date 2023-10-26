import logging

DYNAMIC_SAMPLING_PARAMS = {
    "max_sample_per_config": 8,
    "coefficient_of_variation_threshold": 0.05,
}
MAX_NUMBER_OF_INVOCATION_ATTEMPTS = 5
MAX_TOTAL_SAMPLE_COUNT = 20
MIN_SAMPLE_PER_CONFIG = 4
TERMINATION_THRESHOLD = 3

LOG_LEVEL = logging.WARNING
