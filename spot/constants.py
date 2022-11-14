import os

MEM_SIZE = "Memory Size"
BILLED_DURATION = "Billed Duration"
TIMESTAMP = "timestamp"
COST = "Cost"
RUNTIME = "Runtime"
TIMEOUT = "Timeout"
ARCH = "Architectures"
REGION = "Region"
ERR_VAL = "ErrorValue"
LAST_MODIFIED_MS = "LastModifiedInMs"
REQUEST_ID = "RequestId"

# PRICING
DURATION_PRICE = "duration_price"
REQUEST_PRICE = "request_price"

DB_NAME_PRICING = "pricing"
DB_NAME_CONFIG = "config"
DB_NAME_LOGS = "logs"
# TODO: maybe put config prediction and error into the same database?
DB_NAME_RECOMMENDATION = "recommendation"
DB_NAME_ERROR = "error"
DB_NAME_CONFIG_SUGGESTION = "suggested_config"
DB_ID = "_id"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")


SAMPLE_POINTS = [128, 2048]
MEMORY_RANGE = [128, 3008]
IS_DYNAMIC_SAMPLING_ENABLED = True
TOTAL_SAMPLE_COUNT = 20
RANDOM_SAMPLING = True
RANDOM_SEED = 0
IS_MULTI_FUNCTION = True

ALPHA = 0
NORMAL_SCALE = 100
