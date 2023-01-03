from lmfit import Model, Parameters
from spot.constants import LAMBDA_DURTION_COST, LAMBDA_REQUEST_COST
import numpy as np
from scipy.optimize import curve_fit


class Utility:
    @staticmethod
    def find_minimum_memory_cost(f, params, memory_range):
        mems = np.arange(memory_range[0], memory_range[1] + 1, dtype=np.double)
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
        initial_values, bounds = Utility._guess_initial_values(mems, real_cost)
        popt = curve_fit(Utility.fn, mems, real_cost, p0=initial_values, maxfev=int(1e8), bounds=bounds)[0]
        return Utility.fn, popt

    @staticmethod
    def fn(x, a0, a1, a2, a3, b0, b1):
        return a0 * x + a1 + a2 / (x-b0) + a3 / (x-b1)**2

    @staticmethod
    def fnp(x, **kwargs):
        res = 0
        for i in range(1, kwargs["n"]):
            res -= i * kwargs[f"a{i}"] / (x ** (i + 1))
        return res


    @staticmethod
    def _guess_initial_values(x, y):
        assert len(x) >= 4 and len(x) == len(y)
        a0 = np.max((y[-1] - y[-3]) / (x[-1] - x[-3]), 0.)
        a1 = -a0 * x[-1] + y[-1]
        y2 = y - a0 * x - a1
        a2 = np.max(y2[2] * x[2], 0.)
        y3 = y2 - a2 / x
        a3 = np.max(y3[1] * x[1], 0.)
        return [a0, a1, a2, a3, 0, 0], ([0, -np.inf, 0, 0, -np.inf, -np.inf], [np.inf, np.inf, np.inf, np.inf, 0, 0])
