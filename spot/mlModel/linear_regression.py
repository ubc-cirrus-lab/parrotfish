import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime

from spot.db.db import DBClient
from sklearn.linear_model import LinearRegression

import copy

class LinearRegressionModel:
    def __init__(self, function_name, vendor, url, port):
        self.url = url
        self.port = port
        self.DBClient = DBClient(self.url, self.port) 
        
        self.function_name = function_name
        self.model = None #try to load the latest ML model here if not exists, asssign None
        self.df = pd.DataFrame(columns = ["Runtime", "Timeout", "MemorySize", "Architectures", "Region", "Cost"])
        self.vendor = vendor


    ''' 
    Helper function, used for finding the corresponding configuration and pricing 
    that was in effect when a log is produced on a serverless function trigger
    '''
    def find_associated_index(self, list, field, left, right, target):
        if left > right:
            return -1

        mid = int((right+left)/2)
        if list[mid][field] <= target:
            if mid+1 == len(list):
                return mid
            else:
                if list[mid+1][field] > target:
                    return mid
                else:
                    return self.find_associated_index(list, field, mid+1, right, target)
        else:
            return self.find_associated_index(list, field, left, mid-1, target)
            
    '''
    Fetches config, pricing and log data for the current function
    Associates config, pricing and log files by using timestamping comparison
    Fills dataframe via reformatting the fetched data
    '''
    def fetch_data(self):
        # gets all past configs associated with the current function name
        config_query_result = self.DBClient.execute_query(self.function_name, "config", {}, {"Runtime":1, "Timeout":1, "MemorySize":1, "Architectures":1, "LastModifiedInMs":1, "_id":0})
        configs = []
        for config in config_query_result:
            configs.append(config)
        
        #get all prices for the current function's cloud vendor
        pricing_query_result = self.DBClient.execute_query("pricing", self.vendor, {}, {"request_price":1, "duration_price":1, "region":1, "timestamp":1, "_id":0})
        pricings = []
        for pricing in pricing_query_result:
            pricings.append(pricing)

        # get all logs for this function
        log_query_result = self.DBClient.execute_query(self.function_name, "logs", {}, {"Billed Duration" : 1,"Memory Size":1, "timestamp": 1, "_id":0})
        
        #find the config and pricing to associate with for every log of this function
        for log in log_query_result:
            current_config = self.find_associated_index(configs, "LastModifiedInMs", 0, len(configs)-1, log["timestamp"])
            current_pricing = self.find_associated_index(pricings, "timestamp", 0, len(pricings)-1, log["timestamp"])

            #reformat the dataframe
            if current_config != -1 and current_pricing != -1:
                current_config = copy.deepcopy(configs[current_config])
                current_pricing = copy.deepcopy(pricings[current_pricing])

                new_row = current_config
                del new_row["LastModifiedInMs"]
                new_row["MemorySize"] = log["Memory Size"]
                new_row["Region"] = current_pricing["region"]
                new_row["Cost"] = float(current_pricing["duration_price"]) * float(log["Billed Duration"]) * float(int(log["Memory Size"])/128)

                self.df = self.df.append(new_row, ignore_index=True)
        return
        
    
    def train_model(self):
        #Transform numerical columns to categorical
        self.df.Runtime = pd.Categorical(self.df.Runtime)
        self.df['Runtime'] = self.df.Runtime.cat.codes

        self.df.Architectures = pd.Categorical(self.df.Architectures)
        self.df['Architectures'] = self.df.Architectures.cat.codes

        self.df.Region = pd.Categorical(self.df.Region)
        self.df['Region'] = self.df.Region.cat.codes

        #Create X matrix and Y vector for ML training
        x = self.df[["Runtime", "Timeout", "MemorySize", "Architectures", "Region"]]
        y = self.df["Cost"]

        #Create and train the model
        self.model = LinearRegression()
        self.model.fit(x, y)

        #TODO: save model to db, save the model as binary?

        #Print results and create scatter plot
        print('intercept:', self.model.intercept_)
        print('slope:', self.model.coef_)

        print("Saving the plot as graph")
        self.show_graph(x["MemorySize"],y)
    
    '''
    Predicts the price outcome of given values in our ML model
    '''
    def predict(self, new_x):
        print(self.model.predict(new_x).summary())

    '''
    Creates and saves scatter plot of Memory Size vs Cost per mB data for the current serverless function
    '''
    def show_graph(self, x, y):
        plt.title("Memory Size vs Cost Graph")
        plt.xlabel("Memory(mB)")
        plt.ylabel("Cost per mB($)")

        zipped_list = zip(y,x)
        sorted_zipped_lists = sorted(zipped_list)
        x = [element for _, element in sorted_zipped_lists]
        y = [_ for _, element in sorted_zipped_lists]

        plt.scatter(x, y)
        today = datetime.datetime.now()
        timestamp = today.strftime( '%Y-%m-%dT%H:%M:%S.%f+0000')
        plt.savefig(self.function_name + "-" + timestamp + ".png")

