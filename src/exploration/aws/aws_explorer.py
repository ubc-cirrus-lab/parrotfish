import boto3

from .aws_config_manager import AWSConfigManager
from .aws_cost_calculator import AWSCostCalculator
from .aws_invoker import AWSInvoker
from .aws_log_parser import AWSLogParser
from ..explorer import Explorer


class AWSExplorer(Explorer):
    def __init__(
        self,
        lambda_name: str,
        payload: str,
        max_invocation_attempts: int,
        aws_session: boto3.Session,
        memory_bounds: list = None,
    ):
        super().__init__(
            log_parser=AWSLogParser(),
            config_manager=AWSConfigManager(
                function_name=lambda_name, aws_session=aws_session
            ),
            invoker=AWSInvoker(
                function_name=lambda_name,
                payload=payload,
                max_invocation_attempts=max_invocation_attempts,
                aws_session=aws_session,
            ),
            price_calculator=AWSCostCalculator(
                function_name=lambda_name, aws_session=aws_session
            ),
            memory_bounds=memory_bounds,
            memory_space=set(range(128, 3009)),
        )
