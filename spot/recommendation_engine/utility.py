from lmfit import Model, Parameters
from spot.constants import LAMBDA_DURTION_COST, LAMBDA_REQUEST_COST
import numpy as np
from scipy.optimize import curve_fit


class Utility:
    @staticmethod
    def find_minimum_memory_cost(f, params, memory_range):
        mems = np.arange(memory_range[0], memory_range[1] + 1, dtype=np.double)
        # costs = f(mems, **params) * mems
        costs = f(mems, *params)
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
    def fit_function(datapoints):
        datapoints.sort(key=lambda d: d.memory)
        mems = np.array([x.memory for x in datapoints], dtype=np.double)
        billed_time = np.array([x.billed_time for x in datapoints], dtype=np.double)
        real_cost = mems * billed_time
        initial_values = Utility.guess_initial_values(mems, real_cost)
        popt = curve_fit(Utility.fn, mems, real_cost, p0=initial_values, maxfev=int(1e8))[0]
        return Utility.fn, popt

    @staticmethod
    def fn(x, a0, a1, a2, b):
        return a0 * x + a1 + a2 / (x-b)

    @staticmethod
    def fnp(x, **kwargs):
        res = 0
        for i in range(1, kwargs["n"]):
            res -= i * kwargs[f"a{i}"] / (x ** (i + 1))
        return res


    @staticmethod
    def guess_initial_values(x, y):
        assert len(x) >= 4 and len(x) == len(y)
        a0 = (y[-1] - y[-3]) / (x[-1] - x[-3])
        a1 = -a0 * x[-1] + y[-1]
        y2 = y - a0 * x - a1
        a2 = y2[2] * x[2]
        return [a0, a1, a2, 0]
