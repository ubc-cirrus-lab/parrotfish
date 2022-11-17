import os
import subprocess
import json
import pandas as pd
import numpy as np

from spot.constants import *


class Context:
    def __init__(self):
        self.function_dfs = {}
        self.pricing_df = pd.DataFrame()

    # Creates database for the function name if the doesnt exist already
    def create_function_df(self, function_name):
        self.function_dfs[function_name] = pd.DataFrame()

    def save_invokation_result(self, function_name, result_df):
        old = self.function_dfs.get(function_name, pd.DataFrame())
        self.function_dfs[function_name] = pd.concat([old, result_df])

    def record_pricing(self, row):
        df = pd.DataFrame(row)
        self.pricing_df = pd.concat([self.pricing_df, df])
