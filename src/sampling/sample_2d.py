import numpy as np

from .data_point_2d import DataPoint2D
from typing import Union

class Sample2D:
    """Class for keeping track of the sample."""

    def __init__(self, datapoints: list[DataPoint2D] = None):
        if datapoints is None:
            datapoints = []
        self._datapoints = datapoints

    @property
    def costs(self):
        return np.array((self.cpu_mems[:,0] + self.cpu_mems[:,1]) * self.durations)

    @property
    def durations(self):
        return np.array(
            [datapoint.duration_ms / 1000 for datapoint in self._datapoints], dtype=np.float
        )

    @property
    def cpu_mems(self):
        return np.array(
            [[datapoint.vcpu, datapoint.memory_mb] for datapoint in self._datapoints]
        )

    def update(self, data: Union[DataPoint2D, list]):
        if isinstance(data, list):
            self._datapoints.extend(data)
        elif isinstance(data, DataPoint2D):
            self._datapoints.append(data)
        else:
            raise TypeError(f"{data} must be of type DataPoint or list of DataPoints")

        self._datapoints.sort(key=lambda datapoint: (datapoint.vcpu, datapoint.memory_mb))

    def __len__(self):
        return len(self._datapoints)
