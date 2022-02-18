import json

class BenchmarkConfig:
    def __init__(self, f=None):
        self.function_name : str
        self.vendor : str
        self.region : str
        self.initial_mem_size : int
        self.workload : dict

        if f is not None:
            self.deserialize(f)

    def _set_properties(self, function_name: str, vendor: str, region : str, initial_mem_size: int, workload: dict):
        self.function_name = function_name
        self.vendor = vendor
        self.region = region
        self.initial_mem_size = initial_mem_size
        self.workload = workload

    def deserialize(self, f):
        j_dict = json.load(f)
        self._set_properties(**j_dict)

    def serialize(self):
        return json.dumps(self, default=lambda o: [k for k, v in o.__dict__.iteritems() if type(v) is property], sort_keys=True, indent=4, skipkeys=True)
