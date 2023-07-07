from .sampling_error import SamplingError


class ExplorationError(SamplingError):
    def __init__(self, msg):
        super().__init__(msg)
