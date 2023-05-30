class LambdaInvocationError(Exception):
    def __init__(self, messages):
        self.messages = messages