from spot.prices.aws_price_retriever import AWSPriceRetriever
from spot.logs.aws_log_retriever import AWSLogRetriever
from spot.invocation.aws_function_invocator import AWSFunctionInvocator
from spot.invocation.aws_credentials_fetch import AWSCredentialsFetch
from spot.configs.aws_config_retriever import AWSConfigRetriever
from spot.mlModel.linear_regression import LinearRegressionModel
import json
import time as time
import os


def invoke_function(config_retriever, price_retriever, function_invocator):
    # fetch configs and most up to date prices
    config_retriever.get_latest_config()
    price_retriever.fetch_current_pricing()

    #invoke function
    function_invocator.invoke_all()

def collect_data(log_retriever):
    #retrieve logs
    log_retriever.get_logs()

def train_model(ml_model):
    #train ml model
    ml_model.fetch_data()
    ml_model.train_model()

def main():
    #TODO: move following code to SPOT class constructor

    #Load configuration values from config.json
    config = None
    with open('spot/config.json') as f:
        config = json.load(f)
        with open('spot/workload.json', 'w') as json_file:
            json.dump(config["workload"], json_file)

    #Set environment variables
    aws_creds = AWSCredentialsFetch()
    os.environ["AWS_ACCESS_KEY_ID"] = aws_creds.get_access_key_id()
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_creds.get_secret_access_key()

    #Instantiate SPOT system components
    price_retriever = AWSPriceRetriever(config["DB_URL"], config["DB_PORT"], config["region"])
    log_retriever = AWSLogRetriever(config["function_name"], config["DB_URL"], config["DB_PORT"])
    function_invocator = AWSFunctionInvocator("spot/workload.json", config["function_name"], config["mem_size"], config["region"])
    config_retriever = AWSConfigRetriever(config["function_name"], config["DB_URL"], config["DB_PORT"])
    ml_model = LinearRegressionModel(config["function_name"], config["DB_URL"], config["DB_PORT"])#TODO: Parametrize ML model constructor with factory method

    print("Invoking function: ", config["function_name"])
    #invoke the indicated function
    invoke_function(config_retriever, price_retriever, function_invocator)
    
    print("Sleeping for 1 min to allow logs to propogate")
    #wait 1 min to allow logs to populate in aws
    time.sleep(60)

    print("Retrieve new logs and save in db")
    #collect log data
    collect_data(log_retriever)

    print("Training ML model")
    #train ML model accordingly
    train_model(ml_model)

if __name__ == '__main__':
    main()
