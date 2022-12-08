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

DB_NAME_LOGS = "logs"
# TODO: maybe put config prediction and error into the same database?
DB_NAME_RECOMMENDATION = "recommendation"
DB_NAME_ERROR = "error"
DB_NAME_CONFIG_SUGGESTION = "suggested_config"
DB_ID = "_id"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CTX_DIR = os.path.join(ROOT_DIR, "__context_cache__")

IS_DYNAMIC_SAMPLING_ENABLED = True
IS_MULTI_FUNCTION = True

LAMBDA_DURTION_COST = 0.0000166667
LAMBDA_REQUEST_COST = 0.20 / 1000000

if os.environ.get("SPOT_MODE") == "dev":
    ALPHA = float(os.environ.get("SPOT_ALPHA", 0))
    NORMAL_SCALE = int(os.environ.get("SPOT_NORMAL_SCALE", 100))
    TOTAL_SAMPLE_COUNT = int(os.environ.get("SPOT_SAMPLE_COUNT", 20))
    TERMINATION_CV = float(os.environ.get("SPOT_TERMINATION_CV", 0.3))
    KNOWLEDGE_RATIO = float(os.environ.get("SPOT_KNOWLEDGE_RATIO", 0.2))
    DYNAMIC_SAMPLING_MAX = int(os.environ.get("SPOT_DYNAMIC_SAMPLING_MAX", 5))
    DYNAMIC_SAMPLING_INITIAL_STEP = int(
        os.environ.get("SPOT_DYNAMIC_SAMPLING_INITIAL_STEP", 2)
    )
    OPTIMIZATION_OBJECTIVE = os.environ.get("SPOT_OPTIMIZATION_OBJECTIVE", "normal")
    INITIAL_SAMPLE_MEMORIES = list(
        map(int, os.environ.get("SPOT_INITIAL_SAMPLE_MEMORIES", "128,3008").split(","))
    )

else:
    ALPHA = 0
    NORMAL_SCALE = 100
    TOTAL_SAMPLE_COUNT = 20
    TERMINATION_CV = 0.3
    KNOWLEDGE_RATIO = 0.2
    DYNAMIC_SAMPLING_MAX = 5
    DYNAMIC_SAMPLING_INITIAL_STEP = 2
    OPTIMIZATION_OBJECTIVE = "normal"
    INITIAL_SAMPLE_MEMORIES = [128, 3008]
