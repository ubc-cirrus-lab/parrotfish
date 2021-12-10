from optparse import OptionParser
import sys

from JSONConfigHelper import CheckJSONConfig, ReadJSONConfig
from WorkloadChecker import CheckWorkloadValidity
from GenConfigs import *
from invocator import Invocator

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
    ivk = Invocator(workload)
    # TODO: add loop to invoke with differetn memory settings
    ivk.invoke_all(256)
    return True


if __name__ == '__main__':
    main(sys.argv)
