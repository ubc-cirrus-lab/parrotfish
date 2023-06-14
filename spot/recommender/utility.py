from spot.constants import LAMBDA_DURATION_COST, LAMBDA_REQUEST_COST
import numpy as np
from scipy.optimize import curve_fit

from spot.exceptions.no_memory_left_error import NoMemoryLeftError


class Utility:
    @staticmethod
    def find_minimum_memory_cost(
        f, params, memory_range, execution_time_threshold: float = None
    ):
        mems = np.arange(memory_range[0], memory_range[1] + 1, dtype=np.double)
        costs = f(mems, *params)

        # Handling execution threshold
        if execution_time_threshold is not None:
            filtered_mems = np.array([])
            filtered_costs = np.array([])
            execution_times = costs / mems
            for i in range(len(execution_times)):
                if execution_times[i] <= execution_time_threshold:
                    filtered_mems = np.append(filtered_mems, mems[i])
                    filtered_costs = np.append(filtered_costs, costs[i])
            mems = filtered_mems
            costs = filtered_costs
            if len(mems) == 0:
                raise NoMemoryLeftError()

        min_index = np.argmin(costs)
        return mems[min_index], costs[min_index]

    @staticmethod
    def calculate_cost(duration, memory):
        # TODO: get cost from price retriever
        allocated_memory = 0.0009765625 * memory  # convert MB to GB
        request_compute_time = np.ceil(duration) * 0.001  # convert ms to seconds
        total_compute = allocated_memory * request_compute_time
        compute_charge = LAMBDA_DURATION_COST * total_compute
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
        initial_values = [1000, 10000, 100]
        bounds = ([0, 0, 0], [np.inf, np.inf, np.inf])
        popt = curve_fit(
            Utility.fn,
            mems,
            real_cost,
            p0=initial_values,
            maxfev=int(1e8),
            bounds=bounds,
        )[0]
        return Utility.fn, popt

    @staticmethod
    def fn(x, a0, a1, a2):
        return a0 * x + a1 * np.exp(-x / a2) * x

    @staticmethod
    def fnp(x, **kwargs):
        res = 0
        for i in range(1, kwargs["n"]):
            res -= i * kwargs[f"a{i}"] / (x ** (i + 1))
        return res
