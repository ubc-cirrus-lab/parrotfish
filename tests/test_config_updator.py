import unittest
from botocore.exceptions import ParamValidationError

from spot.invocation.config_updater import ConfigUpdater

class TestConfigUpdate(unittest.TestCase):
    def test_init(self):
        mem = 500
        config = ConfigUpdater('AWSHelloWorld', mem, 'us-east-2')
        self.assertEqual(config.get_mem_size(), mem)
        client_mem = config.client.get_function_configuration(FunctionName='AWSHelloWorld')['MemorySize']
        self.assertEqual(client_mem, mem)

        mem_illegal = 10
        with self.assertRaises(ParamValidationError):
            config = ConfigUpdater('AWSHelloWorld', mem_illegal, 'us-east-2')
        
    def test_set_mem_size(self):
        config = ConfigUpdater('AWSHelloWorld', 128, 'us-east-2')
        mem = 512
        config.set_mem_size(mem)
        self.assertEqual(config.get_mem_size(), mem)
        client_mem = config.client.get_function_configuration(FunctionName='AWSHelloWorld')['MemorySize']
        self.assertEqual(client_mem, mem)
        