import json
from optparse import OptionParser
from requests_futures.sessions import FuturesSession
import sys
import time
import threading
#import requests

from JSONConfigHelper import CheckJSONConfig, ReadJSONConfig
from WorkloadChecker import CheckWorkloadValidity
from EventGenerator import GenericEventGenerator
from GenConfigs import *
from Auth import IAMAuth


def invoke(auth, payload, instance_times):
    st = 0
    after_time, before_time = 0, 0
    session = FuturesSession(max_workers=15)
    
    url = 'https://' + auth.host + '/' + auth.stage + '/' + auth.resource
    for t in instance_times:
        st = t - (after_time - before_time)
        if st > 0:
            # print(st)
            time.sleep(st)
        before_time = time.time()
        future = session.post(url, data=payload, headers=auth.getHeader(payload))
        #r = requests.post(url, params=json.loads(payload), data=json.loads(payload), headers=auth.getHeader(payload))
        #print(r.status_code)
        #print(r.text)
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
            # plt.plot(instance_times[1:], '.', label='rate='+str(workload['instances'][instance]['rate']))
            # plt.xlabel('event number')
            # plt.ylabel('interval')
            # plt.legend()
            # plt.title('Invocation interval for Poisson distribution')
            # plt.hist(instance_times, 14)
            # plt.show()
            threads.append(threading.Thread(target=invoke, args=[auth, payload, instance_times]))
    '''
    os.system("date +%s%N | cut -b1-13 > " + SPOT_ROOT +
              "/test_metadata.out")
    os.system("echo " + options.config_json + " >> " + SPOT_ROOT +
              "/test_metadata.out")
    os.system("echo " + str(event_count) + " >> " + SPOT_ROOT +
              "/test_metadata.out")
    '''

    for thread in threads:
        thread.start()

    return True


if __name__ == '__main__':
    main(sys.argv)
