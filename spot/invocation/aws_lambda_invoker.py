import json
import base64
import time

import botocore
import re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

MEMORY_CONFIG_MAX_RETRIES = 10


class AWSLambdaInvoker:
    """
    Invokes AWS Lambda with the specified config.
    """

    def __init__(self, ctx, aws_session, lambda_name):
        self.lambda_name = lambda_name
        self.client = aws_session.client("lambda")
        self.ctx = ctx

    def invoke(
        self,
        invocation_count,
        parallelism,
        memory_mb,
        payload_filename,
        save_to_ctx=True,
    ):
        """
        Invokes the specified lambda with given memory config.
        Returns pandas DataFrame representing the execution logs
        """
        keys = ["Duration", "Billed Duration", "Max Memory Used", "Memory Size"]

        with open(payload_filename) as f:
            payload = f.read()

        def invoke_sequential(count):
            # TODO: maybe support different payload across invocations?
            result = {key: [] for key in keys}
            for _ in range(count):
                response = self.client.invoke(
                    FunctionName=self.lambda_name,
                    LogType="Tail",
                    Payload=payload,
                )
                log = str(base64.b64decode(response["LogResult"]))
                parsed_log = parse_log(log, keys)
                for key in keys:
                    result[key].append(parsed_log[key])
            return result

        self._check_and_set_memory_value(memory_mb)
        is_memory_config_ok = False

        for _ in range(MEMORY_CONFIG_MAX_RETRIES):
            results = {key: [] for key in keys}
            errors = []
            with ThreadPoolExecutor(max_workers=parallelism) as executor:
                invocation_chunks = [invocation_count // parallelism] * parallelism
                invocation_chunks[-1] += (
                    invocation_count - invocation_count // parallelism * parallelism
                )
                for chunk in invocation_chunks:
                    try:
                        res = executor.submit(invoke_sequential, chunk).result()
                    except _SingleInvocationError as e:
                        errors.append(e.msg)
                        continue
                    except LambdaTimeoutError:
                        errors.append("Lambda timed out")
                        continue
                    except botocore.exceptions.ReadTimeoutError:
                        errors.append("Lambda timed out")
                        continue
                    for key in keys:
                        results[key].extend(res[key])
            if all([m == memory_mb for m in results["Memory Size"]]):
                is_memory_config_ok = True
                break

        if not is_memory_config_ok:
            raise LambdaMemoryConfigError

        if len(errors) != 0:
            raise LambdaInvocationError(errors)

        result_df = pd.DataFrame.from_dict(results)
        if save_to_ctx:
            self.ctx.save_invocation_result(result_df)
        return result_df

    def _check_and_set_memory_value(self, memory_mb):
        config = self.client.get_function_configuration(FunctionName=self.lambda_name)
        if config["MemorySize"] != memory_mb:
            self._set_memory_value(memory_mb)

    def _set_memory_value(self, memory_mb):
        for _ in range(MEMORY_CONFIG_MAX_RETRIES):
            self.client.update_function_configuration(
                FunctionName=self.lambda_name, MemorySize=memory_mb
            )
            waiter = self.client.get_waiter("function_updated")
            waiter.wait(FunctionName=self.lambda_name)
            config = self.client.get_function_configuration(
                FunctionName=self.lambda_name
            )
            if config["MemorySize"] == memory_mb:
                return
        raise LambdaMemoryConfigError


class LambdaInvocationError(Exception):
    def __init__(self, messages):
        self.messages = messages


class _SingleInvocationError(Exception):
    def __init__(self, msg):
        self.msg = msg


class LambdaMemoryConfigError(Exception):
    pass


class LambdaTimeoutError(Exception):
    pass


def parse_log(log, keys):
    res = {}
    # check for timeout
    if "Task timed out after" in log:
        raise LambdaTimeoutError

    # check for errors
    m = re.match(r".*\[ERROR\] (?P<error>.*)END RequestId.*", log)
    if m is not None:
        raise _SingleInvocationError(m["error"])

    # check for keys
    for key in keys:
        m = re.match(rf".*\\t{key}: (?P<duration>[0-9.]+) (ms|MB).*", log)
        res[key] = float(m["duration"])
    return res
