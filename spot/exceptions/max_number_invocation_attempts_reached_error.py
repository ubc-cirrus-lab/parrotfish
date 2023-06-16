class MaxNumberInvocationAttemptsReachedError(Exception):

    def __init__(self):
        super().__init__("Error has been raised while invoking the lambda function. "
                         "Please make sure that the provided function name and configuration are correct!")
