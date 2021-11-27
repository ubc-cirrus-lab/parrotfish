import json
from optparse import OptionParser
from requests_futures.sessions import FuturesSession
import sys
import time
import threading
import requests

from JSONConfigHelper import CheckJSONConfig, ReadJSONConfig
from WorkloadChecker import CheckWorkloadValidity
from EventGenerator import GenericEventGenerator
from GenConfigs import *
from requests_futures.sessions import FuturesSession
from Auth import IAMAuth


def invoke(auth, payload, instance_times):
    st = 0
    after_time, before_time = 0, 0
    session = FuturesSession(max_workers=15)
    
    url = 'https://' + auth.host + '/' + auth.stage + '/' + auth.resource
    for t in instance_times:
        st = t - (after_time - before_time)
        if st > 0:
            time.sleep(st)
        before_time = time.time()
        future = session.post(url, data=payload, headers=auth.getHeader(payload))
        # r = requests.post(url, data=payload, headers=auth.getHeader(payload))
        # print(r.status_code)
        after_time = time.time()

    return True

def main(argv):
    parser = OptionParser()
    parser.add_option("-c", "--config_json", dest="config_json",
                      help="The input json config file describing the synthetic workload.", metavar="FILE")
    (options, args) = parser.parse_args()

    if not CheckJSONConfig(options.config_json):
        return False

    workload = ReadJSONConfig(options.config_json)
    if not CheckWorkloadValidity(workload=workload):
        return False

    [all_events, event_count] = GenericEventGenerator(workload)
    threads = []
    for (instance, instance_times) in all_events.items():
        # function = workload['instances'][instance]['application']
        payload_file = workload['instances'][instance]['payload']
        host = workload['instances'][instance]['host']
        stage = workload['instances'][instance]['stage']
        resource = workload['instances'][instance]['resource']
        auth = IAMAuth(host, stage, resource)

        if payload_file:
            with open(payload_file, 'r') as f:
                payload = json.load(f)
                payload = json.dumps(payload)
        else:
            payload = None

        if workload['instances'][instance]['distribution'] == 'Poisson':
            threads.append(threading.Thread(target=invoke, args=[auth, payload, instance_times]))

    for thread in threads:
        thread.start()

    return True


if __name__ == '__main__':
    main(sys.argv)
