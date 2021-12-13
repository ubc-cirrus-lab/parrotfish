#from prices.aws_price_retriever import AWSPriceRetriever
from logs.aws_log_retriever import AWSLogRetriever
from invocation.aws_function_invocator import AWSFunctionInvocator
from configs.aws_config_retriever import AWSConfigRetriever

def main():
    #price_retriever = AWSPriceRetriever()
    log_retriever = AWSLogRetriever()
    function_invocator = AWSFunctionInvocator()
    config_retriever = AWSConfigRetriever()

    
    #config_retriever.get_latest_config()
    #log_retriever.get_logs()
    #print(price_retriever.get_current_prices())

if __name__ == '__main__':
    main()
