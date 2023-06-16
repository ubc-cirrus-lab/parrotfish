import numpy as np
from spot.pricing import *
from spot.invocation.aws_lambda_invoker import AWSLambdaInvoker
from spot.input_config import InputConfig
from spot.recommender.recommendation_engine import RecommendationEngine
from spot.constants import *
from spot.sampler import Sampler
from spot.sampler.objectives import *
from spot.data_model import *


class Spot:
    def __init__(self, config_dir: str, aws_session):
        # Load configuration values from config.json
        self.config_file_path = os.path.join(config_dir, "config.json")

        payload_file_path = os.path.join(config_dir, "payload.json")
        with open(payload_file_path) as f:
            self.payload = f.read()

        with open(self.config_file_path) as f:
            self.config: InputConfig = InputConfig(f)

        self.last_log_timestamp = None

        # Instantiate SPOT system components
        self.price_calculator = AWSLambdaInvocationPriceCalculator(aws_session, self.config.function_name)

        function_invoker = AWSLambdaInvoker(self.config.function_name, aws_session.client("lambda"))

        fitting_function = FittingFunction(Spot.fn, {})

        objective = NormalObjective(fitting_function, self.config.mem_bounds)
        if OPTIMIZATION_OBJECTIVE == "fit_to_real_cost":
            assert len(INITIAL_SAMPLE_MEMORIES) == 3
            objective = FitToRealCostObjective(fitting_function, self.config.mem_bounds)

        sampler = Sampler(
            invoker=function_invoker,
            memory_range=self.config.mem_bounds,
            payload=self.payload,
            objective=objective,
            price_calculator=self.price_calculator,
            fitting_function=fitting_function
        )

        self.recommendation_engine = RecommendationEngine(
            invoker=function_invoker,
            memory_range=self.config.mem_bounds,
            sampler=sampler,
            fitting_function=fitting_function,
            execution_time_threshold=self.config.execution_time_threshold,
        )

        self.benchmark_name = os.path.basename(config_dir)

    def optimize(self):
        return self.recommendation_engine.run()

    def invoke(self, memory_mb: int, nbr_invocations: int):
        billed_duration = np.arange(nbr_invocations, dtype=np.double)
        for i in range(nbr_invocations):
            df = self.recommendation_engine.invoke_once(memory_mb, self.payload, is_warm=(i > 0))
            billed_duration[i] = df["Billed Duration"][0]
        print(
            "Real cost:", self.price_calculator.calculate_price(memory_mb, billed_duration).mean()
        )

    @staticmethod
    def fn(x, a0, a1, a2):
        return a0 * x + a1 * np.exp(-x / a2) * x
