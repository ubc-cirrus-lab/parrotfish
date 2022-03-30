import concurrent.futures
import json
import os
import time
import threading
import boto3
import botocore

from spot.invocation.JSONConfigHelper import CheckJSONConfig, ReadJSONConfig
from spot.invocation.WorkloadChecker import CheckWorkloadValidity
from spot.invocation.EventGenerator import GenericEventGenerator
from spot.invocation.config_updater import ConfigUpdater


class InvalidWorkloadFileException(Exception):
    pass


class AWSFunctionInvocator:
    """
    Invokes a function based on the parameters specified in a workload json file

    Args:
        workload_path: file path to workload specifications
        function_name: name of the function on lambda
        mem_size: the initial memory size for the serverless function to run
        region: region of the serverless function

    Attributes:
        invoke_cnt: the number of total function invocations of a certain workload setting

    Raises:
        InvalidWorkloadFileException: if the workload file is not of json format or some fields have wrong types
    """

    def __init__(
        self, workload_path: str, function_name: str, mem_size: int, region: str
    ) -> None:
        self._read_workload(workload_path)
        self._workload_path: str = os.path.dirname(workload_path)
        self._config = ConfigUpdater(function_name, mem_size, region)
        self._config.set_mem_size(mem_size)
        self._all_events, _ = GenericEventGenerator(self._workload)
        self._futures = []
        self._thread = []
        self.invoke_cnt = 0

    def _read_workload(self, path: str) -> None:
        if not CheckJSONConfig(path):
            raise InvalidWorkloadFileException
        workload = ReadJSONConfig(path)
        if not CheckWorkloadValidity(workload=workload):
            raise InvalidWorkloadFileException
        self._workload = workload

    def _append_threads(self, instance: str, instance_times: list) -> None:
        payload_file = self._workload["instances"][instance]["payload"]
        application = self._workload["instances"][instance]["application"]
        client = boto3.client("lambda")

        try:
            f = open(os.path.join(self._workload_path, payload_file), "r")
        except IOError:
            f = None
        payload = json.load(f) if f else None
        self.payload = payload

        self._threads.append(
            threading.Thread(
                target=self._invoke, args=[client, application, payload, instance_times]
            )
        )

    def _invoke(
        self,
        client: "botocore.client.logs",
        function_name: str,
        payload: list,
        instance_times: list,
    ) -> bool:
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            # TODO: store input and invocation info to db
            st = 0
            after_time, before_time = 0, 0
            cnt = 0

            for t in instance_times:
                st = t - (after_time - before_time)
                if st > 0:
                    time.sleep(st)
                input_data = json.dumps(
                    payload[cnt % len(payload)] if payload else None
                )
                cnt += 1
                before_time = time.time()
                future = executor.submit(
                    client.invoke, FunctionName=function_name, Payload=input_data
                )
                self.invoke_cnt += 1
                self._futures.append(future)
                after_time = time.time()

        return True

    def invoke_all(self, mem: int = -1) -> None:
        """Invoke the function with user specified inputs and parameters asynchronously"""
        self.invoke_cnt = 0
        self._threads = []
        for (instance, instance_times) in self._all_events.items():
            self._config.set_instance(
                self._workload["instances"][instance]["application"]
            )
            if mem != -1:
                self._config.set_mem_size(mem)
            self._append_threads(instance, instance_times)
        for thread in self._threads:
            thread.start()
        for thread in self._threads:
            thread.join()
        for future in self._futures:
            res = future.result()
