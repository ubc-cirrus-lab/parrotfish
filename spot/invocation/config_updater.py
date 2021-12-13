import requests
import boto3

class InstanceNotSetException(Exception):
    pass

class ConfigUpdater:
    def __init__(self, ins=None, region='us-west-1', mem=128):
        self.mem_size = mem
        self.instance = ins
        self.client = boto3.client('lambda', region_name=region)

    def set_mem_size(self, mem):
        self.mem_size = mem

    def get_mem_size(self):
        return self.mem_size

    def set_instance(self, ins):
        self.instance = ins

    def set_mem_size(self, mem):
        self.mem_size = mem
        if not self.instance:
            raise InstanceNotSetException
        res = self.client.update_function_configuration(
            FunctionName=self.instance,
            MemorySize=self.mem_size
        )
        print(res)
