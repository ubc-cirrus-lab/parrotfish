import json
from typing import Optional

from spot.constants import DEFAULT_MEM_BOUNDS


class BenchmarkConfig:
    def __init__(self, f=None):
        self.function_name: str
        self.vendor: str
        self.region: str
        self.mem_size: int
        self.mem_bounds: list
        self.nickname: str
        self.execution_time_threshold: float

        if f is not None:
            self.deserialize(f)

    def __setitem__(self, index, value):
        self.__dict__[index] = value

    def get_dict(self):
        return self.__dict__

    def _set_properties(
        self,
        function_name: str,
        vendor: str,
        region: str,
        random_seed: int,
        nickname: str,
        execution_time_threshold: float = None,
        mem_bounds: Optional[list] = None,
    ):
        self.function_name = function_name
        self.vendor = vendor
        self.region = region
        self.mem_bounds = DEFAULT_MEM_BOUNDS if mem_bounds is None else mem_bounds
        self.random_seed = random_seed
        self.nickname = nickname
        self.execution_time_threshold = execution_time_threshold

    def deserialize(self, f):
        try:
            j_dict = json.load(f)
        except:
            print("Failed to deserialize the given file")
            raise IOError
        self._set_properties(**j_dict)

    def serialize(self):
        return json.dumps(self.__dict__, skipkeys=True, indent=4, sort_keys=True)
