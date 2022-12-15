from lmfit import Model, Parameters
from spot.constants import LAMBDA_DURTION_COST, LAMBDA_REQUEST_COST
import numpy as np


class AggregatedData:
    def __init__(self, memory, billed_time):
        self.memory = memory
        self.billed_time = billed_time


class Utility:
    @staticmethod
    def find_minimum_memory_cost(f, params, memory_range):
        mems = np.arange(memory_range[0], memory_range[1] + 1, dtype=float)
        costs = Utility.calculate_cost(f(mems, **params), mems)
        min_index = np.argmin(costs)
        return mems[min_index], costs[min_index]

    @staticmethod
    def calculate_cost(duration, memory):
        # TODO: get cost from price retriever
        allocated_memory = 0.0009765625 * memory  # convert MB to GB
        request_compute_time = np.ceil(duration) * 0.001  # convert ms to seconds
        total_compute = allocated_memory * request_compute_time
        compute_charge = LAMBDA_DURTION_COST * total_compute
        return LAMBDA_REQUEST_COST + compute_charge

    @staticmethod
    def cv(l):
        return np.std(l, ddof=1) / np.mean(l)

    @staticmethod
    def check_function_validity(f, params, memory_range):
        if all(v >= 0 for v in params.values()):
            return True
        mems = np.arange(memory_range[0], memory_range[1] + 1, dtype=float)
        return np.all(f(mems, **params) >= 0)

    @staticmethod
    def fit_function(datapoints, degree):
        f = Utility.fn
        fmodel = Model(f)
        params = Parameters()
        params.add("n", value=degree, vary=False)
        params.add("a0", value=20)
        params.add("a1", value=100000)
        for i in range(2, degree):
            params.add(f"a{i}", value=1000)
        aggregated_datapoints = Utility.aggregate_data(datapoints)
        fresult = fmodel.fit(
            [x.billed_time for x in aggregated_datapoints],
            x=[x.memory for x in aggregated_datapoints],
            params=params,
        )
        fparams = fresult.params.valuesdict()
        return f, fparams

    @staticmethod
    def aggregate_data(data):
        aggregated_data = []
        for x in data:
            aggregated_data.append(AggregatedData(x.memory, x.billed_time))
        aggregated_data.sort(key=lambda x: x.memory)
        return aggregated_data

    @staticmethod
    def fn(x, **kwargs):
        res = kwargs["a0"]
        for i in range(1, kwargs["n"]):
            res += kwargs[f"a{i}"] / (x**i)
        return res

    @staticmethod
    def fnp(x, **kwargs):
        res = 0
        for i in range(1, kwargs["n"]):
            res -= i * kwargs[f"a{i}"] / (x ** (i + 1))
        return res
