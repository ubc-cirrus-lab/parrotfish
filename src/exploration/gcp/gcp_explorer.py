from .gcp_config_manager import GCPConfigManager
from .gcp_cost_calculator import GCPCostCalculator
from .gcp_invoker import GCPInvoker
from .gcp_log_parser import GCPLogParser
from ..explorer import Explorer


class GCPExplorer(Explorer):
    def __init__(
        self,
        function_name: str,
        payload: str,
        credentials: any,
        memory_bounds: list = None,
    ):
        log_parser = GCPLogParser()
        super().__init__(
            log_parser=log_parser,
            config_manager=GCPConfigManager(
                function_name=function_name, credentials=credentials
            ),
            invoker=GCPInvoker(
                function_name=function_name,
                payload=payload,
                log_keys=log_parser.log_parsing_keys,
                credentials=credentials,
            ),
            price_calculator=GCPCostCalculator(
                function_name=function_name, region=credentials.region
            ),
            memory_space=set([2**i for i in range(7, 14)]),
            memory_bounds=memory_bounds,
        )
