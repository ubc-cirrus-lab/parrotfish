from dataclasses import dataclass
import numpy as np
from scipy.optimize import curve_fit


@dataclass
class FittingFunction:
    """Class for keeping track of the parametric function."""
    function: callable
    params: any

    def __call__(self, memories: np.array):
        return self.function(memories, *self.params)

    def fit_function(self, datapoints: list):
        datapoints.sort(key=lambda d: d.memory)
        memories = np.array([x.memory for x in datapoints], dtype=np.double)
        billed_time = np.array([x.billed_time for x in datapoints], dtype=np.double)
        real_cost = memories * billed_time
        initial_values = [1000, 10000, 100]
        bounds = ([0, 0, 0], [np.inf, np.inf, np.inf])
        self.params = curve_fit(
            self.function,
            memories,
            real_cost,
            p0=initial_values,
            maxfev=int(1e8),
            bounds=bounds,
        )[0]
