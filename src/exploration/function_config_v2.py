from dataclasses import dataclass


@dataclass
class FunctionConfigV2:
    """Class for keeping track of the function's configuration before exploration."""

    memory_mb: int
    timeout: int
    cpu: float
