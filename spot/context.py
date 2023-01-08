import pandas as pd
import pickle

from spot.constants import *


class Context:
    def __init__(self):
        self.invocation_df = pd.DataFrame()
        self.pricing_df = pd.DataFrame()
        self.final_df = None
        if CACHED_DATA_CSV_PATH is None:
            self.cached_df = None
        else:
            self.cached_df = pd.read_csv(CACHED_DATA_CSV_PATH)

    def save_invocation_result(self, result_df):
        self.invocation_df = pd.concat([self.invocation_df, result_df])

    def save_final_result(self, final_df):
        self.final_df = final_df

    def record_cached_data(self, cached_df):
        self.cached_df = pd.concat([self.cached_df, cached_df])

    def record_pricing(self, row):
        df = pd.DataFrame(row)
        self.pricing_df = pd.concat([self.pricing_df, df])

    def _save_supplementary_info(self, function_name: str, optimization_s):
        self.final_df["Benchmark Name"] = function_name
        self.final_df["Alpha"] = ALPHA
        self.final_df["Normal Scale"] = NORMAL_SCALE
        self.final_df["Sample Count"] = TOTAL_SAMPLE_COUNT
        self.final_df["Termination CV"] = TERMINATION_CV
        self.final_df["Knowledge Ratio"] = KNOWLEDGE_RATIO
        self.final_df["Dynamic Sampling Max"] = DYNAMIC_SAMPLING_MAX
        self.final_df["Dynamic Sampling Initial Step"] = DYNAMIC_SAMPLING_INITIAL_STEP
        self.final_df["Optimization Objective"] = OPTIMIZATION_OBJECTIVE
        self.final_df["Initial Sample Memories"] = f"{INITIAL_SAMPLE_MEMORIES}"
        self.final_df["Termination Logic"] = TERMINATION_LOGIC
        self.final_df["Termination Threshold"] = TERMINATION_THRESHOLD
        self.final_df["minimum_sampling"] = MINIMUM_SAMPLING
        self.final_df["handle_cold_start"] = HANDLE_COLD_START
        self.final_df["dynamic_sampling_enabled"] = HANDLE_COLD_START
        if optimization_s:
            self.final_df["Time Elapsed in Seconds"] = optimization_s

        self.invocation_df["Benchmark Name"] = function_name
        self.invocation_df["Alpha"] = ALPHA
        self.invocation_df["Normal Scale"] = NORMAL_SCALE
        self.invocation_df["Sample Count"] = TOTAL_SAMPLE_COUNT
        self.invocation_df["Termination CV"] = TERMINATION_CV
        self.invocation_df["Knowledge Ratio"] = KNOWLEDGE_RATIO
        self.invocation_df["Dynamic Sampling Max"] = DYNAMIC_SAMPLING_MAX
        self.invocation_df[
            "Dynamic Sampling Initial Step"
        ] = DYNAMIC_SAMPLING_INITIAL_STEP

    def save_context(self, fn_name, ctx_file, elapsed):
        if CACHED_DATA_CSV_PATH is not None:
            cached_df = self.cached_df
            cached_df.to_csv(CACHED_DATA_CSV_PATH)
            self.cached_df = None

        with open(ctx_file, "wb") as f:
            self._save_supplementary_info(fn_name, elapsed)
            pickle.dump(self, f)