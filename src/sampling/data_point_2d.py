from dataclasses import dataclass


@dataclass
class DataPoint2D:
    """Class for keeping track of the result of one exploration."""

    vcpu: float
    memory_mb: int
    duration_ms: int
