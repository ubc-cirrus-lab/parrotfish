class LambdaTimeoutError(Exception):
    def __init__(self):
        super().__init__("Lambda time out error. The execution time limit is reached.")
