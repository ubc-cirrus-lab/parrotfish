from unittest import mock

from src.exploration import Explorer


class MockExplorer(Explorer):
    def __init__(self):
        log_parser = mock.Mock()
        log_parser.parse_log.return_value = 18180

        config_manager = mock.Mock()
        config_manager.set_config.return_value = {"MemorySize": 128, "Timeout": 300}

        invoker = mock.Mock()
        invoker.invoke.return_value = "invocation result"

        price_calculator = mock.Mock()
        price_calculator.calculate_price.return_value = 10

        super().__init__(
            config_manager=config_manager,
            invoker=invoker,
            log_parser=log_parser,
            price_calculator=price_calculator,
            memory_space=set(range(128, 3009)),
            payload="payload",
        )
        self._memory_config_mb = 128
