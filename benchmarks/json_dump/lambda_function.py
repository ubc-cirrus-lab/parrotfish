# Taken from https://github.com/ddps-lab/serverless-faas-workbench by Jeongchul Kim and Kyungyong Lee
import json
from urllib.request import urlopen
from time import time


def lambda_handler(event, context):
    link = event["link"]  # https://github.com/jdorfman/awesome-json-datasets

    start = time()
    f = urlopen(link, timeout=2)
    data = f.read().decode("utf-8")
    network = time() - start

    start = time()
    json_data = json.loads(data)
    str_json = json.dumps(json_data, indent=4)
    latency = time() - start

    print(str_json)
    return {"network": network, "serialization": latency}
