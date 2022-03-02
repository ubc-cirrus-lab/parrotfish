import json

class BenchmarkConfig:
    def __init__(self, f=None):
        self.function_name : str
        self.vendor : str
        self.region : str
        self.mem_size : int
        self.workload : dict

        if f is not None:
            self.deserialize(f)

    def __setitem__(self, index, value):
        self.__dict__[index] = value

    def get_dict(self):
        return self.__dict__

    def _set_properties(self, function_name: str, vendor: str, region : str, mem_size: int, workload: dict):
        self.function_name = function_name
        self.vendor = vendor
        self.region = region
        self.mem_size = mem_size
        self.workload = workload

    def deserialize(self, f):
        j_dict = json.load(f)
        self._set_properties(**j_dict)

    def serialize(self):
        return json.dumps(self.__dict__, skipkeys=True, indent=4, sort_keys=True)
