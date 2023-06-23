from dataclasses import dataclass


@dataclass
class DataPoint:
    """Class for keeping track of the datapoints to be sampled."""
    memory: int
    billed_time: int

