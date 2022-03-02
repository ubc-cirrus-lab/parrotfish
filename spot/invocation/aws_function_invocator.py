import concurrent.futures
import json
import os
import time
import threading
import boto3

from spot.invocation.JSONConfigHelper import CheckJSONConfig, ReadJSONConfig
from spot.invocation.WorkloadChecker import CheckWorkloadValidity
from spot.invocation.EventGenerator import GenericEventGenerator
from spot.invocation.config_updater import ConfigUpdater


class InvalidWorkloadFileException(Exception):
    pass


class AWSFunctionInvocator:
    futures = []

    def __init__(self, workload, function_name, mem_size, region):
        self.workload = self._read_workload(workload)
        self.workload_path : str = os.path.dirname(workload)
        self.config = ConfigUpdater(function_name, mem_size, region)
        self.config.set_mem_size(mem_size)
        self.threads = []
        self.all_events, _ = GenericEventGenerator(self.workload)

    def _read_workload(self, path):
        if not CheckJSONConfig(path):
            raise InvalidWorkloadFileException
        workload = ReadJSONConfig(path)
        if not CheckWorkloadValidity(workload=workload):
            raise InvalidWorkloadFileException
        return workload

    def _append_threads(self, instance, instance_times):
        payload_file = self.workload["instances"][instance]["payload"]
        application = self.workload["instances"][instance]["application"]
        client = boto3.client("lambda")

        try:
            f = open(os.path.join(self.workload_path, payload_file), "r")
        except IOError:
            f = None
            # raise PayloadFileNotFoundException
        payload = json.load(f) if f else None

        self.threads.append(
            threading.Thread(
                target=self._invoke, args=[client, application, payload, instance_times]
            )
        )

    def _invoke(self, client, application, payload, instance_times):
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
                    client.invoke, FunctionName=application, Payload=input_data
                )
                self.futures.append(future)
                after_time = time.time()

        return True

    def invoke_all(self, mem=-1):
        for (instance, instance_times) in self.all_events.items():
            self.config.set_instance(
                self.workload["instances"][instance]["application"]
            )
            if mem != -1:
                self.config.set_mem_size(mem)
            self._append_threads(instance, instance_times)
        for thread in self.threads:
            thread.start()
        for thread in self.threads:
            thread.join()
        for future in self.futures:
            res = future.result()
