from asyncio import futures
import json
from requests_futures.sessions import FuturesSession
import sys
import time
import threading

# import requests

from spot.invocation.JSONConfigHelper import CheckJSONConfig, ReadJSONConfig
from spot.invocation.WorkloadChecker import CheckWorkloadValidity
from spot.invocation.EventGenerator import GenericEventGenerator
from spot.invocation.iam_auth import IAMAuth
from spot.invocation.config_updater import ConfigUpdater


class InvalidWorkloadFileException(Exception):
    pass


class AWSFunctionInvocator:
    futures = []

    def __init__(self, workload, function_name, mem_size, region):
        self.workload = self._read_workload(workload)
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
        host = self.workload["instances"][instance]["host"]
        stage = self.workload["instances"][instance]["stage"]
        resource = self.workload["instances"][instance]["resource"]
        auth = IAMAuth(host, stage, resource)

        try:
            f = open(payload_file, "r")
        except IOException:
            f = None
            # raise PayloadFileNotFoundException
        payload = json.load(f) if f else None

        self.threads.append(
            threading.Thread(target=self._invoke, args=[auth, payload, instance_times])
        )

    def _invoke(self, auth, payload, instance_times):
        # TODO: store input and invocation info to db
        st = 0
        after_time, before_time = 0, 0
        session = FuturesSession(max_workers=15)
        cnt = 0

        url = "https://" + auth.host + "/" + auth.stage + "/" + auth.resource
        for t in instance_times:
            st = t - (after_time - before_time)
            if st > 0:
                time.sleep(st)
            input_data = payload[cnt % len(payload)] if payload else None
            cnt += 1
            before_time = time.time()
            future = session.post(
                url,
                params=input_data,
                data=input_data,
                headers=auth.getHeader(json.dumps(input_data)),
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
