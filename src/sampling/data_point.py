from dataclasses import dataclass


@dataclass
class DataPoint:
    """Class for keeping track of the result of one exploration."""

    memory_mb: int
    duration_ms: int
