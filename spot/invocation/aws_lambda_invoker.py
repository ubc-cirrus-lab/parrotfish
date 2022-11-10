import json
import base64
import boto3
import re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

class AWSLambdaInvoker:
    """
    Invokes AWS Lambda with the specified config.
    """
    def __init__(self, lambda_name):
        self.lambda_name = lambda_name
        self.client = boto3.client("lambda")

    def invoke(self, invocation_count, parallelism, memory_mb, payload):
        """
        Invokes the specified lambda with given memory config.
        Returns pandas DataFrame representing the execution logs
        """
        keys = ["Duration", "Billed Duration", "Max Memory Used"]

        def invoke_sequential(count):
            # TODO: maybe support different payload across invocations?
            result = {key: [] for key in keys}
            for _ in range(count):
                response = self.client.invoke(
                    FunctionName=self.lambda_name,
                    LogType="Tail",
                    Payload=payload,
                )
                log = str(base64.b64decode(response['LogResult']))
                parsed_log = parse_log(log, keys)
                for key in keys:
                    result[key].append(parsed_log[key])
            return result

        self._check_and_set_memory_value(memory_mb)
        results = {key: [] for key in keys}
        with ThreadPoolExecutor(max_workers=parallelism) as executor:
            invocation_chunks = [invocation_count // parallelism] * parallelism
            invocation_chunks[-1] += invocation_count - invocation_count // parallelism * parallelism
            for chunk in invocation_chunks:
                res = executor.submit(invoke_sequential, chunk).result()
                for key in keys:
                    results[key].extend(res[key])
        return pd.DataFrame.from_dict(results)

    def _check_and_set_memory_value(self, memory_mb):
        config = self.client.get_function_configuration(FunctionName=self.lambda_name)
        if config["MemorySize"] != memory_mb:
            self._set_memory_value(memory_mb)
        config = self.client.get_function_configuration(FunctionName=self.lambda_name)
        assert(config["MemorySize"] == memory_mb)

    def _set_memory_value(self, memory_mb):
        self.client.update_function_configuration(FunctionName=self.lambda_name, MemorySize=memory_mb)


def parse_log(log, keys):
    res = {}
    for key in keys:
        m = re.match(rf'.*\\t{key}: (?P<duration>[0-9.]+) (ms|MB).*', log)
        res[key] = float(m['duration'])
    return res

# if __name__ == "__main__":
#     invoker = AWSLambdaInvoker("DNAVisualization")
#     p = bytes(json.dumps({"gen_file_name": "sequence_2.gb"}), "utf-8")
#     invoker.invoke(3, 1, 256, p)
