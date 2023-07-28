from .sampling_error import SamplingError


class NoMemoryLeftError(SamplingError):
    def __init__(self):
        super().__init__("No memory left in the memory space to explore with.")
