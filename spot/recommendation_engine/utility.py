from lmfit import Model, Parameters
from spot.constants import LAMBDA_DURTION_COST, LAMBDA_REQUEST_COST
import numpy as np


class Utility:
    @staticmethod
    def find_minimum_memory_cost(f, params, memory_range):
        mems = np.arange(memory_range[0], memory_range[1] + 1, dtype=np.double)
        # costs = f(mems, **params) * mems
        costs = f(mems, **params)
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
        mems = np.arange(memory_range[0], memory_range[1] + 1)
        return np.all(f(mems, **params) >= 0)

    @staticmethod
    def fit_function(datapoints, degree):
        params = Parameters()
        params.add("n", value=degree, vary=False)
        params.add("a0", min=0, value=20)
        for i in range(1, degree):
            params.add(f"a{i}", min=0, value=10000)
        f = Utility.fn
        fmodel = Model(f)
        datapoints.sort(key=lambda d: d.memory)
        mems = np.array([x.memory for x in datapoints])
        billed_time = np.array([x.billed_time for x in datapoints])
        fresult = fmodel.fit(
            billed_time * mems,
            x=mems,
            params=params,
        )
        fparams = fresult.params.valuesdict()
        return f, fparams

    @staticmethod
    def fn(x, **kwargs):
        res = 0
        for i in range(0, kwargs["n"]):
            res += kwargs[f"a{i}"] * np.power(x, -i+2)
        return res

    @staticmethod
    def fnp(x, **kwargs):
        res = 0
        for i in range(1, kwargs["n"]):
            res -= i * kwargs[f"a{i}"] / (x ** (i + 1))
        return res
