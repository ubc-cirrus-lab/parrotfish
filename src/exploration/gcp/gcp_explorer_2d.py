from .gcp_config_manager_v2 import GCPConfigManagerV2
from .gcp_cost_calculator import GCPCostCalculator
from .gcp_invoker_v2 import GCPInvokerV2
from ..explorer_2d import Explorer2D


class GCPExplorer2D(Explorer2D):
    def __init__(
        self,
        function_name: str,
        credentials: any,
        max_invocation_attempts: any,
        payload: str = None,
        cpu_bounds: list = None,
        memory_bounds: list = None,
    ):
        # Create CPU-Memory space based on GCP documentation: https://cloud.google.com/run/docs/configuring/services/cpu
        cpu_memory_dict = {}
        cpu_values = [0.08, 0.21, 0.34, 0.47, 0.61, 0.74, 0.87, 1.0, 2.0, 4.0]
        for cpu in cpu_values:
            if cpu < 0.5:
                memory_list = list(range(128, 513, 128))
            elif 0.5 <= cpu < 1.0:
                memory_list = list(range(128, 1025, 128))
            elif 1.0 <= cpu < 4.0:
                memory_list = list(range(128, 4097, 128))
            elif cpu == 4.0:
                memory_list = list(range(2048, 4097, 128))
            cpu_memory_dict[cpu] = memory_list
        super().__init__(
            payload=payload,
            config_manager=GCPConfigManagerV2(
                function_name=function_name, credentials=credentials
            ),
            invoker=GCPInvokerV2(
                function_name=function_name,
                credentials=credentials,
                max_invocation_attempts=max_invocation_attempts,
            ),
            price_calculator=GCPCostCalculator(
                function_name=function_name, region=credentials.region
            ),
            cpu_mem_space=set([(item[0], m) for item in cpu_memory_dict.items() for m in item[1]]),
            cpu_bounds = cpu_bounds,
            memory_bounds=memory_bounds,
        )
