import os
import subprocess
import json
import pandas as pd
import numpy as np

from spot.constants import *


class Context:  # TODO(joe): rename to Context
    def __init__(self):
        self.function_dfs = {}
        self.pricing_df = pd.DataFrame()

    # Creates database for the function name if the doesnt exist already
    def create_function_df(self, function_name):
        self.function_dfs[function_name] = pd.DataFrame()

    def record_pricing(self, row):
        df = pd.DataFrame(row)
        self.pricing_df = pd.concat([self.pricing_df, df])
