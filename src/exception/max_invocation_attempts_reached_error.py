from .invocation_error import InvocationError


class MaxInvocationAttemptsReachedError(InvocationError):
    def __init__(self, msg: str = None, duration_ms: int = None):
        if not msg:
            msg = "Error has been raised while invoking the lambda function. Max number of invocations' attempts " \
                  "reached."
        super().__init__(msg)
        self.duration_ms = duration_ms
