import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

IS_DYNAMIC_SAMPLING_ENABLED = False
HANDLE_COLD_START = False

LAMBDA_DURATION_COST = 0.0000166667
LAMBDA_REQUEST_COST = 0.20 / 1000000
DEFAULT_MEM_BOUNDS = [128, 3008]

MAX_NUMBER_INVOCATION_ATTEMPTS = 5

ACCEPTED_MEMORY_RANGE_AWS = (128, 3008)

# Maybe we don't need SPOT_MODE, only used in the ec2 instance.
if os.environ.get("SPOT_MODE") == "dev":
    ALPHA = float(os.environ.get("SPOT_ALPHA", 0))
    NORMAL_SCALE = int(os.environ.get("SPOT_NORMAL_SCALE", 100))
    TERMINATION_CV = float(os.environ.get("SPOT_TERMINATION_CV", 0.3))
    DYNAMIC_SAMPLING_MAX = int(os.environ.get("SPOT_DYNAMIC_SAMPLING_MAX", 5))
    DYNAMIC_SAMPLING_INITIAL_STEP = int(
        os.environ.get("SPOT_DYNAMIC_SAMPLING_INITIAL_STEP", 2)
    )
    OPTIMIZATION_OBJECTIVE = os.environ.get(
        "SPOT_OPTIMIZATION_OBJECTIVE", "fit_to_real_cost"
    )
    INITIAL_SAMPLE_MEMORIES = list(
        map(int, os.environ.get("SPOT_INITIAL_SAMPLE_MEMORIES", "128,3008").split(","))
    )
    TERMINATION_THRESHOLD = float(os.environ.get("SPOT_TERMINATION_THRESHOLD", 1.5))

else:
    ALPHA = 0
    NORMAL_SCALE = 100
    TOTAL_SAMPLE_COUNT = 10
    TERMINATION_CV = 0.05
    KNOWLEDGE_RATIO = 0.2
    DYNAMIC_SAMPLING_MAX = 5
    DYNAMIC_SAMPLING_INITIAL_STEP = 2
    OPTIMIZATION_OBJECTIVE = "fit_to_real_cost"
    INITIAL_SAMPLE_MEMORIES = [128, 1024, 3008]
    TERMINATION_LOGIC = "knowledge_of_optimal"
    TERMINATION_THRESHOLD = 1.5
