from spot.prices.aws_price_retriever import AWSPriceRetriever
from spot.logs.aws_log_retriever import AWSLogRetriever
from spot.invocation.aws_function_invocator import AWSFunctionInvocator
from spot.configs.aws_config_retriever import AWSConfigRetriever
from spot.mlModel.linear_regression import LinearRegressionModel
import json
import time as time
import os


def invoke_and_collect_data(config_retriever, log_retriever, price_retriever, function_invocator, function_name):
    # fetch configs and most up to date prices
    # TODO: possibly disallow any config changes here, like an atomic operation
    config_retriever.get_latest_config()
    price_retriever.fetch_current_pricing()

    #invoke function
    function_invocator.invoke_all()

    #wait 1 min to allow logs to populate in aws
    time.sleep(60)

    #retrieve logs
    log_retriever.get_logs()

    #train ml model
    # ml_model= LinearRegressionModel("AWSHelloWorld", "localhost", 27017)
    ml_model= LinearRegressionModel("formplug-dev-receive", "localhost", 27017)
    ml_model.fetch_data()
    ml_model.train_model()

def main():
    config = None
    with open('spot/config.json') as f:
        config = json.load(f)
        os.environ["AWS_ACCESS_KEY_ID"] = config["AWS_ACCESS_KEY_ID"]
        os.environ["AWS_SECRET_ACCESS_KEY"] = config["AWS_SECRET_ACCESS_KEY"]
        with open('spot/workload.json', 'w') as json_file:
            json.dump(config["workload"], json_file)

    price_retriever = AWSPriceRetriever(config["DB_URL"], config["DB_PORT"])
    log_retriever = AWSLogRetriever(config["function_name"], config["DB_URL"], config["DB_PORT"])
    function_invocator = AWSFunctionInvocator("spot/workload.json", 256)
    config_retriever = AWSConfigRetriever(config["function_name"], config["DB_URL"], config["DB_PORT"])

    invoke_and_collect_data(config_retriever, log_retriever, price_retriever, function_invocator, config["function_name"])

if __name__ == '__main__':
    main()
