from src.exception import FunctionENOMEM


class FunctionTimeoutError(FunctionENOMEM):
    def __init__(self, duration_ms: int = None):
        super().__init__(
            "Serverless function time out error. The execution time limit is reached.",
            duration_ms,
        )
