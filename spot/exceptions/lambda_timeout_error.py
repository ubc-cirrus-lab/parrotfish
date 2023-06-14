class LambdaTimeoutError(Exception):
    def __str__(self):
        return "Lambda time out error. The execution time limit is reached."
