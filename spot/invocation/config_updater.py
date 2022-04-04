import boto3


class InstanceNotSetException(Exception):
    pass


class ConfigUpdater:
    mem_size = -1

    def __init__(self, function_name: str, mem: int, region: str) -> None:
        self._function_name = function_name
        self.client = boto3.client("lambda", region_name=region)
        self.set_mem_size(mem)

    def get_mem_size(self) -> None:
        return self.mem_size

    def set_instance(self, function_name: str) -> None:
        self._function_name = function_name

    def set_mem_size(self, mem: int) -> None:
        if self.mem_size == mem:
            return
        self.mem_size = mem
        if not self._function_name:
            raise InstanceNotSetException
        self.client.update_function_configuration(
            FunctionName=self._function_name, MemorySize=self.mem_size
        )
        waiter = self.client.get_waiter("function_updated")
        waiter.wait(FunctionName=self._function_name)
