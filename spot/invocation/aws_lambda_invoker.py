import base64
import sys
import time
from ..logs import *
from .function_invoker import FunctionInvoker
from ..context import Context


class AWSLambdaInvoker(FunctionInvoker):
    """Implementation of the FunctionInvoker for AWS Lambda functions.

    This class provides operations to invoke the AWS lambda function with a specific configuration.
    """

    def __init__(self, ctx: Context, aws_session, lambda_name: str):
        super().__init__(lambda_name,
                         log_keys=["Duration", "Billed Duration", "Max Memory Used", "Memory Size"],
                         client=aws_session.client("lambda"),
                         context=ctx)

    def invoke_sequential(self, count: int, payload: str):
        """For a fixed configuration invoking the lambda function multiple times and returning a dictionary with keys
        those defined in log_keys and values the parsed results of the invocation in lists.

        Args:
            count: The number of invocations.
            payload: Payload to the lambda function.
        """
        # For a fixed config (mem value) we invoke the lambda function multiple times (count times)
        # We return a dictionary of with keys the ones in keys variable and values lists of the different
        # results from the invocations
        # TODO: maybe support different payload across invocations?
        result = {key: [] for key in self.log_keys}
        for _ in range(count):
            interval = 1
            while True:
                try:
                    # response here is the lambda function response which includes the log, the log contains
                    # the execution time and a lots of metrics, we do care only of the metrics in self.log_keys variable.
                    # Tail here means all the logs
                    # payload is the payload of the function
                    # region is already in the client object.
                    response = self.client.invoke(
                        FunctionName=self.function_name,
                        LogType="Tail",
                        Payload=payload,
                    )
                except:
                    # AWS has limitation on the number of requests to invoke the function. We sleep for an amount
                    # of time to mitigate this problem. We loop an infinite of time and
                    # when no exception is raised we break.
                    print(
                        "possible Too Many Request Error. Retrying", file=sys.stderr
                    )
                    time.sleep(interval)
                    interval *= 2
                else:
                    break
            log = str(base64.b64decode(response["LogResult"]))
            parsed_log = AWSLogParser().parse_log(log, self.log_keys)
            for key in self.log_keys:
                result[key].append(parsed_log[key])

        return result

    def check_and_set_memory_value(self, memory_mb):
        config = self.client.get_function_configuration(FunctionName=self.function_name)
        if config["MemorySize"] != memory_mb:
            self._set_memory_value(memory_mb)

    def _set_memory_value(self, memory_mb):
        while True:
            self.client.update_function_configuration(
                FunctionName=self.function_name, MemorySize=memory_mb
            )
            waiter = self.client.get_waiter("function_updated")
            waiter.wait(FunctionName=self.function_name)
            config = self.client.get_function_configuration(
                FunctionName=self.function_name
            )
            if config["MemorySize"] == memory_mb:
                return
