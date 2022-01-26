from cgitb import handler
import json
from warnings import catch_warnings
from requests_futures.sessions import FuturesSession
import sys
import time
import threading
#import requests

from spot.invocation.JSONConfigHelper import CheckJSONConfig, ReadJSONConfig
from spot.invocation.WorkloadChecker import CheckWorkloadValidity
from spot.invocation.EventGenerator import GenericEventGenerator
# from spot.invocation.GenConfigs import *
from spot.invocation.iam_auth import IAMAuth
from spot.invocation.config_updater import ConfigUpdater

class InvalidWorkloadFileException(Exception):
    pass

class PayloadFileNotFoundException(Exception):
    pass

class PayloadFileNotSpecifiedException(Exception):
    pass

class SetMemoryFailureException(Exception):
    pass

class AWSFunctionInvocator:
    def __init__(self, workload, mem=128):
        self.workload = self._read_workload(workload)
        self.config = ConfigUpdater(region = "us-east-2")#TODO:parametrize this with config file
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
        try:
            payload_file = self.workload['instances'][instance]['payload']
        except KeyError:
            raise PayloadFileNotSpecifiedException
            payload_file = None
        host =self.workload['instances'][instance]['host']
        stage = self.workload['instances'][instance]['stage']
        resource = self.workload['instances'][instance]['resource']
        auth = IAMAuth(host, stage, resource)
        
        try:
            f = open(payload_file, 'r')
        except IOException:
            raise PayloadFileNotFoundException
            # f = None

        payload = json.dumps(json.load(f))

        # if f:
        #     payload = json.dumps(json.load(f))
        # else:
        #     payload = None

        self.threads.append(threading.Thread(target=self._invoke, args=[auth,payload,instance_times]))


    def _start_threads(self):
        for thread in self.threads:
            thread.start()

    def _handle_payload(self, payload, cnt):
        instance = payload[cnt%len(payload)]
        input_data = instance['data']
        try :
            mem = instance['config']['memory']
            self.config.set_mem_size(mem)
            print('memory set to ', mem)
        except Exception:
            raise SetMemoryFailureException
        return input_data



    def _invoke(self, auth, payload, instance_times):
        # TODO: store input and invocation info to db
        st = 0
        after_time, before_time = 0, 0
        session = FuturesSession(max_workers=15)

        url = 'https://' + auth.host + '/' + auth.stage + '/' + auth.resource
        cnt = 0

        if payload: 
            payload = json.loads(payload)
        for t in instance_times:
            if payload:
                input_data = self._handle_payload(payload, cnt)
                cnt+=1
            else:
                input_data = None
            print('current data: ', input_data)

            st = t - (after_time - before_time)
            if st > 0:
                time.sleep(st)
            before_time = time.time()
            future = session.post(url, params=input_data, data=input_data, headers=auth.getHeader(json.dumps(input_data)))
            #r = requests.post(url, params=json.loads(input_data), data=json.loads(input_data), headers=auth.getHeader(input_data))
            #print(r.status_code)
            #print(r.text)
            after_time = time.time()

        return True


    def invoke_all(self, mem=128):
        for (instance, instance_times) in self.all_events.items():
            self.config.set_instance(self.workload['instances'][instance]['application'])
            self.config.set_mem_size(mem)
            self._append_threads(instance, instance_times)
        self._start_threads()
