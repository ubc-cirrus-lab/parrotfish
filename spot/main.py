#from prices.aws_price_retriever import AWSPriceRetriever
from logs.aws_log_retriever import AWSLogRetriever
from invocation.aws_function_invocator import AWSFunctionInvocator
from configs.aws_config_retriever import AWSConfigRetriever

def main():
    #price_retriever = AWSPriceRetriever()
    log_retriever = AWSLogRetriever()
    function_invocator = AWSFunctionInvocator()
    config_retriever = AWSConfigRetriever()

    
    #config_retriever.get_aws_configs()
    #config_retriever.save_to_db()
    #log_retriever.get_aws_logs()
    #print(price_retriever.get_current_prices())

if __name__ == '__main__':
    main()
