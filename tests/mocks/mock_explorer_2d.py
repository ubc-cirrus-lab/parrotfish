from unittest import mock

from src.exploration import Explorer2D

class MockExplorer2D(Explorer2D):
    def __init__(self):
        config_manager = mock.Mock()
        config_manager.set_config.return_value = {"MemorySize": 128, "CpuSize": 0.08}

        invoker = mock.Mock()
        invoker.invoke.return_value = 18180

        price_calculator = mock.Mock()
        price_calculator.calculate_price.return_value = 10

        super().__init__(
            config_manager=config_manager,
            invoker=invoker,
            price_calculator=price_calculator,
            cpu_mem_space=set([(0.08, m1) for m1 in range(128, 896, 128)] + [(0.21, m2) for m2 in range(896, 1665, 128)]),
            payload="payload",
        )
        self._cpu_config = 0.08
        self._memory_config_mb = 128