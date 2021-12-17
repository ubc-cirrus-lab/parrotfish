import numpy as np
from sklearn.linear_model import LinearRegression

class LinearRegressionModel:
    def __init__(self, function_name):
        self.function_name = function_name
        self.model = None #try to load the latest ML model here if not exists, asssign None
        self.x = None
        self.y = None

    def fetch_data():
        # get all of the parameters here to X
        # get the price to Y
        # assign these variables to class variables x and y respectively
        pass
        
    def train_model():
        self.model = LinearRegression()
        self.model.fit(self.x, self.y) #change this to our variables
        #save model to db
        #save the model as binary?
        print('intercept:', self.model.intercept_)
        print('slope:', self.model.coef_)
    
    def predict(new_x):
        print(self.model.predict(new_x).summary())

