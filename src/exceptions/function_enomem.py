from .invocation_error import InvocationError


class FunctionENOMEM(InvocationError):
    def __init__(self, msg: str = None, duration_ms: int = None):
        if msg is None:
            msg = "The memory configured is not enough for the function's execution."
        super().__init__(msg, duration_ms)
