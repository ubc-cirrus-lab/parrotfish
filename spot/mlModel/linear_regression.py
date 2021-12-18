import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
from spot.db.db import DBClient
#from sklearn.linear_model import LinearRegression

class LinearRegressionModel:
    def __init__(self, function_name, url, port):
        self.url = url
        self.port = port
        self.DBClient = DBClient(self.url, self.port) 
        
        self.function_name = function_name
        self.model = None #try to load the latest ML model here if not exists, asssign None
        self.x = None
        self.y = None


    def find_associated_index(self, list, field, left, right, target):
        if left > right:
            return -1

        mid = int((right+left)/2)
        if int(list[mid][field]) <= target:
            if mid+1 == len(list):
                return mid
            else:
                if int(list[mid+1][field]) > target:
                    return mid
                else:
                    return self.find_associated_index(list, field, mid+1, right, target)
        else:
            return self.find_associated_index(list, field, left, mid-1, target)
            

    def fetch_data(self):
        config_query_result = self.DBClient.execute_query(self.function_name, "config", {}, {"Runtime":1, "Timeout":1, "MemorySize":1, "Architectures":1, "LastModifiedInMs":1, "_id":0})
        configs = []
        for config in config_query_result:
            configs.append(config)
        
        pricings = []

        # get the price to Y
        log_query_result = self.DBClient.execute_query(self.function_name, "logs", {}, {"Billed Duration" : 1, "timestamp": 1, "_id":0})
        for log in log_query_result:
            #for every log, find the config and pricing to associate with

            current_config = self.find_associated_index(configs, "LastModifiedInMs", 0, len(configs)-1, log["timestamp"])
            if current_config == -1:
                print("No config record found for this log")
            else:
                print("Config found")
                current_config = configs[current_config]
            
            current_pricing = self.find_associated_index(pricings, "timestamp", 0, len(pricings)-1, log["timestamp"])
            if current_pricing == -1:
                print("No pricing record found for this log")
            else:
                print("Pricing found")
                current_config = pricings[current_pricing]

        # assign these variables to class variables x and y respectively
        return
        
    
    def train_model(self):
        self.model = LinearRegression()
        self.model.fit(self.x, self.y) #change this to our variables
        #save model to db
        #save the model as binary?
        print('intercept:', self.model.intercept_)
        print('slope:', self.model.coef_)
    
    
    def predict(new_x):
        print(self.model.predict(new_x).summary())

a = LinearRegressionModel("AWSHelloWorld", "localhost", 27017)
a.fetch_data()