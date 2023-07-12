from unittest import mock

from src.exploration import Explorer


class MockExplorer(Explorer):
    def __init__(self):
        log_parser = mock.Mock()
        log_parser.parse_log.return_value = 18180

        price_calculator = mock.Mock()
        price_calculator.calculate_price.return_value = 10

        super().__init__(
            function_name="example_function",
            payload="payload",
            log_parser=log_parser,
            price_calculator=price_calculator,
            memory_space=set(range(128, 3009))

        )
        self._memory_config_mb = 128

    def check_and_set_memory_config(self, memory_mb: int) -> dict:
        return {}

    def invoke(self) -> str:
        return (
            "b'START RequestId: 03d92713-a4b2-4b07-a07a-653087817262 "
            "Version: $LATEST\\n"
            "END RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\n"
            "REPORT RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\"
            "tDuration: 18179.84 ms\\"
            "tBilled Duration: 18180 ms\\"
            "tMemory Size: 512 MB\\"
            "tMax Memory Used: 506 MB\\t\\n'"
        )
