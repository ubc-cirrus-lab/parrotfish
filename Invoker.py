import json
from optparse import OptionParser
import os
from requests_futures.sessions import FuturesSession
import sys
import time
import threading
# import boto3

# from Logger import ScriptLogger
from JSONConfigHelper import CheckJSONConfig, ReadJSONConfig
from WorkloadChecker import CheckWorkloadValidity
from EventGenerator import GenericEventGenerator
from GenConfigs import *
from requests_futures.sessions import FuturesSession
from Auth import getHeader, APIHOST, canonical_uri

# logger = ScriptLogger('invoker', 'ivk.log')
# lambda_client = boto3.client('lambda')
RESULT = 'false'


def invoke(endpoint, payload, instance_times):
    st = 0
    after_time, before_time = 0, 0
    session = FuturesSession(max_workers=15)
    # TODO: make it dynamic from user input
    # url = 'https://55gmzhl9w6.execute-api.us-west-1.amazonaws.com/default/test-hw'
    url = APIHOST + canonical_uri 
    # + '/' + endpoint
    parameters = {'blocking': False, 'result': RESULT}
    for t in instance_times:
        st = t - (after_time - before_time) 
        if st > 0:
            time.sleep(st)
        before_time = time.time()
        # res = lambda_client.invoke(FunctionName=function,
        #                     InvocationType='Event', #async
        #                     LogType='None',
        #                     Payload=payload)
        future = session.post(url, data=payload, headers=getHeader(payload))
        # r = requests.post(url, data=payload, headers=getHeader(payload))
        # print(r.text)
        after_time = time.time()

    return True

def main(argv):
    # logger.info("Workload Invoker started")
    # print("Log file -> logs/SWI.log")
    parser = OptionParser()
    parser.add_option("-c", "--config_json", dest="config_json",
                      help="The input json config file describing the synthetic workload.", metavar="FILE")
    (options, args) = parser.parse_args()

    if not CheckJSONConfig(options.config_json):
        # logger.error("You should specify a JSON config file using -c option!")
        return False
    
    workload = ReadJSONConfig(options.config_json)
    if not CheckWorkloadValidity(workload=workload):
        return False

    [all_events, event_count] = GenericEventGenerator(workload)
    threads = []
    for (instance, instance_times) in all_events.items():
        function = workload['instances'][instance]['application']
        endpoint = workload['instances'][instance]['endpoint']
        payload_file = workload['instances'][instance]['payload']
        
        if payload_file:
            with open(payload_file, 'r') as f:
                payload = json.load(f)
                payload = json.dumps(payload)
        else:
            payload = None
        
        if workload['instances'][instance]['distribution'] == 'Poisson':
            threads.append(threading.Thread(target=invoke, args=[endpoint, payload, instance_times]))

    # logger.info("Test started")
    for thread in threads:
        thread.start()
    # logger.info("Test ended")

    return True


if __name__ == '__main__':
    main(sys.argv)
