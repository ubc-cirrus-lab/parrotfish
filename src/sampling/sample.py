import numpy as np

from .data_point import DataPoint


class Sample:
    """Class for keeping track of the sample."""

    def __init__(self, datapoints: list = None):
        if datapoints is None:
            datapoints = []
        self._datapoints = datapoints

    @property
    def costs(self):
        return np.array(self.memories * self.durations)

    @property
    def durations(self):
        return np.array(
            [datapoint.duration_ms for datapoint in self._datapoints], dtype=np.float
        )

    @property
    def memories(self):
        return np.array(
            [datapoint.memory_mb for datapoint in self._datapoints], dtype=np.int
        )

    def update(self, data: DataPoint or list):
        if isinstance(data, list):
            self._datapoints.extend(data)
        elif isinstance(data, DataPoint):
            self._datapoints.append(data)
        else:
            raise TypeError(f"{data} must be of type DataPoint or list of DataPoints")

        self._datapoints.sort(key=lambda datapoint: datapoint.memory_mb)

    def __len__(self):
        return len(self._datapoints)
