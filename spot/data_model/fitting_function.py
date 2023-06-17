from dataclasses import dataclass
import numpy as np
from scipy.optimize import curve_fit


@dataclass
class FittingFunction:
    """Class for keeping track of the parametric function.

    Attributes:
        function (callable): the function we want to fit to the sample.
        params (np.array): parameters of the function.
        bounds (tuple): Lower and upper bounds on parameters.
    """
    function: callable
    params: np.array
    bounds: tuple

    def __call__(self, memories: np.array):
        return self.function(memories, *self.params)

    def fit(self, datapoints: list) -> None:
        """Use non-linear least squares to fit a function to the datapoints.
        Optimize values for the parameters so that the sum of the squared residuals is minimized.

        Args:
            datapoints (list): list of the sampled datapoints.

        Raises:
            ValueError: if datapoints contains invalid data.
            RuntimeError: if least-squares minimization fails.
        """
        datapoints.sort(key=lambda d: d.memory)
        memories = np.array([datapoint.memory for datapoint in datapoints], dtype=int)
        billed_time = np.array([datapoint.billed_time for datapoint in datapoints], dtype=float)
        real_cost = memories * billed_time

        self.params = curve_fit(
            f=self.function,
            xdata=memories,
            ydata=real_cost,
            maxfev=int(1e8),
            p0=self.params,
            bounds=self.bounds,
        )[0]
