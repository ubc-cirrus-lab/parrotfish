import requests
import boto3
import time

class InstanceNotSetException(Exception):
    pass

class ConfigUpdater:
    def __init__(self, ins, mem, region):
        self.mem_size = mem
        self.instance = ins
        self.client = boto3.client('lambda', region_name=region)

    def get_mem_size(self):
        return self.mem_size

    def set_instance(self, ins):
        self.instance = ins

    def set_mem_size(self, mem):
        if not self.instance:
            raise InstanceNotSetException
        if self.mem_size == mem:
            return
        res = self.client.update_function_configuration(
            FunctionName=self.instance,
            MemorySize=self.mem_size
        )
        waiter = self.client.get_waiter('function_updated')
        waiter.wait(FunctionName=self.instance)
        self.mem_size = mem
