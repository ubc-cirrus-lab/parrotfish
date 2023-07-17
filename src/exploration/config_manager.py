from abc import ABC, abstractmethod


class ConfigManager(ABC):
    """This class provides the operations to manage the serverless function's configuration."""
    def __init__(self, function_name: str):
        self.function_name = function_name
        self.initial_config = None

    @property
    @abstractmethod
    def max_timeout_quota(self) -> int:
        """Max timeout quota for the lambda service associated with the user account."""
        pass

    @abstractmethod
    def set_config(self, memory_mb: int, timeout: int = None) -> any:
        """Updates the serverless function's configuration by setting the memory value to @memory_mb.

        Args:
            memory_mb (int): The memory size in MB.
            timeout (int): The function's timeout is seconds.

        Raises:
            FunctionConfigError: If getting or updating the function's configuration fails.
        """
        pass

    def reset_config(self) -> None:
        """Resets the function's configuration to it's initial state."""
        self.set_config(self.initial_config.memory_mb, self.initial_config.timeout)
