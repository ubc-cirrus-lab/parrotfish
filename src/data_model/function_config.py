from dataclasses import dataclass


@dataclass
class FunctionConfig:
    """Class for keeping track of the function's configuration before exploration."""
    memory_mb: int
    timeout: int
