import os
import subprocess
import json
import pandas as pd
import numpy as np

from spot.constants import *


class Context:
    def __init__(self):
        self.function_df = pd.DataFrame()
        self.pricing_df = pd.DataFrame()
        self.final_df = None

    def save_invocation_result(self, result_df):
        self.function_df = pd.concat([self.function_df, result_df])

    def save_final_result(self, final_df):
        self.final_df = final_df

    def record_pricing(self, row):
        df = pd.DataFrame(row)
        self.pricing_df = pd.concat([self.pricing_df, df])
