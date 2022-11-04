import datetime
import numpy as np
from abc import ABC, abstractmethod
from spot.benchmark_config import BenchmarkConfig
from spot.db.db import DBClient
from spot.invocation.config_updater import ConfigUpdater
from spot.mlModel.ml_model_base_class import MlModelBaseClass
from spot.visualize.Plot import Plot
from spot.constants import *

SAMPLE_POINTS = [128, 2048]
MEMORY_RANGE = [128, 3008]
IS_DYNAMIC_SAMPLING_ENABLED = True
TOTAL_SAMPLE_COUNT = 20
ALPHA = 0.01
NORMAL_SCALE = 100
RANDOM_SAMPLING = True
RANDOM_SEED = 0
LAMBDA_DURTION_COST = 0.0000166667
LAMBDA_REQUEST_COST = 0.20 / 1000000


class Sampler:
    def __init__(self, invocator):
        self.function_invocator = invocator
        self.datapoints = []
        self.sampled_datapoints = []
        self.sampled_points = 0
        self.fitted_function = None
        self.function_parameters = {}
        self.function_degree = 2
        self.objective = NormalObjective(self)
        self.logger = Logger()

    def get_function(self):
        return self.fitted_function, self.function_parameters

    def run(self):
        self.initial_sample()
        self.sampled_points = 2
        while len(self.sampled_datapoints) < TOTAL_SAMPLE_COUNT and self.objective.ratio > 0.2:
            x = self.choose_sample_point()
            self.sample(x)
            self.sampled_points += 1
            self.function_degree = self.sampled_points
            self.fitted_function, self.function_parameters = Utility.fit_function(self.sampled_datapoints,
                                                                                  degree=self.function_degree)
            while Utility.check_function_validity(self.fitted_function, self.function_parameters) is False:
                self.function_degree -= 1
                self.fitted_function, self.function_parameters = Utility.fit_function(self.sampled_datapoints,
                                                                                      degree=self.function_degree)
            self.exctract_logs()
        minimum_memory, minimum_cost = Utility.find_minimum_memory_cost(self.fitted_function, self.function_parameters)
        nearest_memory = min([d.memory for d in self.datapoints], key=lambda x: abs(x - minimum_memory))

    def initial_sample(self):
        for x in SAMPLE_POINTS:
            self.sample(x)
        self.fitted_function, self.function_parameters = Utility.fit_function(self.sampled_datapoints,
                                                                              degree=self.function_degree)
        self.exctract_logs()

    def exctract_logs(self):
        total_cost = 0
        mape = Utility.mape(self.fitted_function, self.function_parameters, [x.memory for x in self.datapoints],
                            [x.billed_time for x in self.datapoints])
        for datapoint in self.sampled_datapoints:
            total_cost += datapoint.cost
        self.logger.add_cost(total_cost)
        self.logger.add_mape(mape)

    def show_results(self, min_hline=0, function_hline=0, use_multi_function=True, dynamic_sampling=True):
        global ALPHA
        global IS_MULTI_FUNCTION
        global IS_DYNAMIC_SAMPLING_ENABLED
        IS_MULTI_FUNCTION = use_multi_function
        IS_DYNAMIC_SAMPLING_ENABLED = dynamic_sampling
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15, 4))
        ALPHA = 0.01

        for color in ['red', 'blue', 'green', 'orange']:
            self.run()
            logging.info(
                f'Sample points (α={ALPHA}): {list(dict.fromkeys([x.memory for x in self.sampled_datapoints]))}')

            axes[0].plot([i for i in range(2, self.sampled_points + 1)],
                         [cost / 10000 for cost in self.logger.costs], label=f'α = {ALPHA}', marker='X', color=color,
                         alpha=0.5)
            axes[0].set_ylabel('Cost (¢)')
            axes[0].set_xlabel('Sample Point #')

            axes[1].plot([i for i in range(2, self.sampled_points + 1)],
                         self.logger.mapes, label=f'α = {ALPHA}', marker='X', color=color, alpha=0.5)
            axes[1].set_ylabel('MAPE value (%)')
            axes[1].set_xlabel('Sample Point #')
            axes[1].set_ylim(0, 100)

            axes[2].plot([cost / 10000 for cost in self.logger.costs], self.logger.mapes, label=f'α = {ALPHA}',
                         marker='X', color=color, alpha=0.5)
            axes[2].set_ylabel('MAPE value (%)')
            axes[2].set_xlabel('Cost (¢)')
            axes[2].set_ylim(0, 100)
            ALPHA /= 10
            if color != 'orange':
                self._reset()

        if min_hline > 0:
            axes[1].axhline(y=min_hline, color="red", linestyle="--", label='Minimum Possible MAPE')
        if function_hline > 0:
            axes[1].axhline(y=function_hline, color="black", linestyle="--", label=f'Mimimum Attained MAPE')

        for ax in axes:
            ax.legend()
        fig.tight_layout()
        fig.subplots_adjust(top=0.88)
        plt.show()

    def sample(self, x):
        values = [self.get_sample_value(x) for _ in range(2)]
        if IS_DYNAMIC_SAMPLING_ENABLED:
            while len(values) < 5 and Utility.cv(values) > 0.3:
                values.append(self.get_sample_value(x))
        return values

    def _reset(self):
        self.sampled_datapoints = []
        self.fitted_function = None
        self.function_degree = 2
        self.sampled_points = 0
        self.function_parameters = []
        self.objective = NormalObjective(self)
        self.logger = Logger()

    def choose_sample_point(self):
        max_value = MEMORY_RANGE[0]
        max_obj = np.inf
        for value in self.remainder_memories():
            obj = self.objective.get_value(value)
            if obj < max_obj:
                max_value = value
                max_obj = obj
        return max_value

    def get_sample_value(self, x):
        self.function_invocator.invoke_all(mem=x)
        candids = [d for d in self.datapoints if d.memory == x and d not in self.sampled_datapoints]
        if len(candids) == 0:
            raise ValueError(f'No datapoint with memory {x} found')

        index = random.randint(0, len(candids) - 1) if RANDOM_SAMPLING else 0
        self.sampled_datapoints.append(candids[index])
        self.objective.update_knowledge(candids[index])
        return candids[index].billed_time

    def remainder_memories(self):
        memories = set([datapoint.memory for datapoint in self.datapoints])
        sampled_memories = set([datapoint.memory for datapoint in self.sampled_datapoints])
        remainder = [x for x in memories if x not in sampled_memories]
        return remainder


class Logger:
    def __init__(self):
        self.costs = []
        self.mapes = []

    def add_cost(self, cost):
        self.costs.append(cost)

    def add_mape(self, mape):
        self.mapes.append(mape)


class Utility:
    def find_minimum_memory_cost(f, params):
        min_cost = np.inf
        min_memory = 0
        for memory in range(MEMORY_RANGE[0], MEMORY_RANGE[1] + 1):
            cost = Utility.calculate_cost(f(memory, **params), memory)
            if cost < min_cost:
                min_cost = cost
                min_memory = memory
        return min_memory, min_cost

    def calculate_cost(duration, memory):
        return np.ceil(duration) * 2.1e-9 * (memory / 128)
        # allocated_memory = 0.0009765625 * memory                    # convert MB to GB
        # request_compute_time = np.ceil(duration) * 0.001            # convert ms to seconds
        # total_compute = allocated_memory * request_compute_time
        # compute_charge = LAMBDA_DURTION_COST * total_compute
        # return LAMBDA_REQUEST_COST + compute_charge

    def cv(l):
        return np.std(l, ddof=1) / np.mean(l)

    def check_function_validity(f, params):
        if all(v >= 0 for v in params.values()):
            return True
        for x in range(MEMORY_RANGE[0], MEMORY_RANGE[1] + 1):
            if f(x, **params) < 0:
                return False
        return True

    def fit_function(datapoints, degree):
        f = Utility.fn
        fmodel = Model(f)
        params = Parameters()
        params.add('n', value=degree, vary=False)
        params.add('a0', value=20)
        params.add('a1', value=100000)
        for i in range(2, degree):
            params.add(f'a{i}', value=1000)
        aggregated_datapoints = Utility.aggregate_data(datapoints)
        fresult = fmodel.fit([x.billed_time for x in aggregated_datapoints],
                             x=[x.memory for x in aggregated_datapoints], params=params)
        fparams = fresult.params.valuesdict()
        return f, fparams

    def aggregate_data(data):
        aggregated_data = []
        for memory_value in [x.memory for x in data]:
            billed_times = []
            for d in data:
                if d.memory == memory_value:
                    billed_times.append(d.billed_time)
            aggregated_data.append(AggregatedData(memory_value, np.median(billed_times)))
        return aggregated_data

    def f1(x, a0, a1):
        return a0 + a1 / x

    def fn(x, **kwargs):
        res = kwargs['a0']
        for i in range(1, kwargs['n']):
            res += kwargs[f'a{i}'] / (x ** i)
        return res

    def find_closest(x, l):
        memories = [datapoint.memory for datapoint in l]
        diff = [abs(x - memory) for memory in memories]
        index = np.asarray(diff).argmin()
        return l[index].memory

    def mape(f, f_params, xs, ys):
        res = [abs((y - f(x, **f_params)) / y) for x, y in zip(xs, ys)]
        return 100 * np.sum(res) / len(xs)

    def get_normal_value(x, mean, std, ratio):
        return ratio * stats.norm.pdf(x, mean, std)

    def normalize(knowledge):
        sum = np.sum(list(knowledge.values()))
        for k, v in knowledge.items():
            knowledge[k] = v / sum


class Objective(ABC):
    def __init__(self, sampler):
        self.sampler = sampler

    def normalized_cost(self, x):
        return self.sampler.fitted_function(x, **self.sampler.function_parameters) * x / self._min_cost()

    def normalized_duration(self, x):
        return self.sampler.fitted_function(x, **self.sampler.function_parameters) / self._max_duration()

    def _max_duration(self):
        max_duration = 0
        for memory_value in range(MEMORY_RANGE[0], MEMORY_RANGE[1] + 1):
            duration = self.sampler.fitted_function(memory_value, **self.sampler.function_parameters)
            if duration > max_duration:
                max_duration = duration
        return max_duration

    def _max_cost(self):
        max_cost = 0
        for memory_value in range(MEMORY_RANGE[0], MEMORY_RANGE[1] + 1):
            cost = self.sampler.fitted_function(memory_value, **self.sampler.function_parameters) * memory_value
            if cost > max_cost:
                max_cost = cost
        return max_cost

    def _min_cost(self):
        min_cost = np.inf
        for memory_value in range(MEMORY_RANGE[0], MEMORY_RANGE[1] + 1):
            cost = self.sampler.fitted_function(memory_value, **self.sampler.function_parameters) * memory_value
            if cost < min_cost:
                min_cost = cost
        return min_cost

    @abstractmethod
    def get_value(self, x):
        pass

    @abstractmethod
    def update_knowledge(self, x):
        pass


class NormalObjective(Objective):
    def __init__(self, sampler):
        super().__init__(sampler)
        self.knowledge_values = {}
        for x in range(MEMORY_RANGE[0], MEMORY_RANGE[1] + 1):
            self.knowledge_values[x] = 0
        self.ratio = 1

    def get_value(self, x):
        return self.knowledge_values[x] + ALPHA * self.normalized_cost(x)

    def update_knowledge(self, x):
        for key, _ in self.knowledge_values.items():
            self.knowledge_values[key] += Utility.get_normal_value(key, x.memory, NORMAL_SCALE, self.ratio)
        self.ratio *= 1 / sum(list(self.knowledge_values.values()))
        Utility.normalize(self.knowledge_values)


class RecommendationEngine:
    def __init__(
            self,
            config_file_path: str,
            config: BenchmarkConfig,
            model: MlModelBaseClass,
            db: DBClient,
            benchmark_dir: str,
    ) -> None:
        self.config_file_path = config_file_path
        self._model = model
        self.new_config = config
        self.db = db
        self.plotter = Plot(self.new_config.function_name, self.db, benchmark_dir)
        self.x_min = None
        self.y_min = None

    """get optimal mem config from the model"""

    def recommend(self) -> int:
        self.x_min, self.y_min = self._model.get_optimal_config()
        print("Best memory config: ", self.x_min, "  ", "Cost: ", self.y_min)
        return int(round(self.x_min, 0))

    def get_pred_cost(self) -> float:
        return self.y_min

    def update_config(self) -> None:
        # Get the new recommended config
        self.new_config.mem_size = self.recommend()

        # Save the updated configurations
        with open(self.config_file_path, "w") as f:
            f.write(self.new_config.serialize())

        # Update the memory config on AWS with the newly suggested memory size
        ConfigUpdater(
            self.new_config.function_name,
            self.new_config.mem_size,
            self.new_config.region,
        )
        timestamp = datetime.datetime.now()

        # Save model config suggestions
        self.db.add_document_to_collection(
            self.new_config.function_name,
            "suggested_configs",
            self.new_config.get_dict(),
        )

    def plot_config_vs_epoch(self) -> None:
        self.plotter.plot_config_vs_epoch()

    def plot_error_vs_epoch(self) -> None:
        self.plotter.plot_error_vs_epoch()
