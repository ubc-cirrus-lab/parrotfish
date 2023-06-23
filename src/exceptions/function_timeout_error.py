class FunctionTimeoutError(Exception):
    def __init__(self):
        super().__init__("Serverless function time out error. The execution time limit is reached.")

    def __str__(self):
        return self.args[0]
