import boto3


class InstanceNotSetException(Exception):
    pass


class ConfigUpdater:
    def __init__(self, function_name, mem, region):
        self.mem_size = mem
        self._function_name = function_name
        self.client = boto3.client("lambda", region_name=region)

    def get_mem_size(self):
        return self.mem_size

    def set_instance(self, ins):
        self._function_name = ins

    def set_mem_size(self, mem):
        if self.mem_size == mem:
            return 
        self.mem_size = mem
        if not self._function_name:
            raise InstanceNotSetException
        self.client.update_function_configuration(
            FunctionName=self._function_name, MemorySize=self.mem_size
        )
        waiter = self.client.get_waiter('function_updated')
        waiter.wait(FunctionName=self._function_name)

